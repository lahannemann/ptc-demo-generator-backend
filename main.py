import traceback

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from itsdangerous import Signer

from dotenv import load_dotenv

import uuid
import time

from openapi_client.exceptions import ServiceException, UnauthorizedException, NotFoundException

from apis.cb_client.cb_api_client import CBApiClient
from services.delete_all_tracker_data import DeleteAllTrackerData
from services.test_step_generator import TestStepGenerator
from services.top_level_item_generator import TopLevelItemGenerator
from services.traceability_generator import TraceabilityGenerator
from services.delete_all_project_data import DeleteAllProjectData
from services.batch_item_generation import BatchItemGeneration
from services.field_updater import FieldUpdater
from services.status_updater import StatusUpdater

app = FastAPI()
load_dotenv()

# Allow requests from your frontend
origins = [
    "http://localhost:5173",
    "https://gentle-cliff-027fd3d0f.1.azurestaticapps.net",
    "https://demogeneratorserver.proudtree-ef764c79.eastus.azurecontainerapps.io",
]

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # or ["*"] to allow all origins (less secure)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory session store
session_store = {}

# Signer for secure session IDs
signer = Signer("your-secret-key")

SESSION_EXPIRATION_SECONDS = 1800  # 30 minutes


@app.middleware("http")
async def add_session_id(request: Request, call_next):
    # Never create sessions on CORS preflight
    if request.method == "OPTIONS":
        return await call_next(request)

    session_id = request.cookies.get("session_id")
    expired = False

    if session_id:
        try:
            signer.unsign(session_id.encode())
            session_data = session_store.get(session_id)
            if session_data:
                created_at = session_data.get("created_at", 0)
                if time.time() - created_at > SESSION_EXPIRATION_SECONDS:
                    expired = True
        except Exception:
            expired = True

    new_session = False
    if not session_id or expired:
        raw_id = str(uuid.uuid4())
        session_id = signer.sign(raw_id).decode()
        session_store[session_id] = {"created_at": time.time()}
        new_session = True

    # Make session id available during this same request
    request.state.session_id = session_id

    response = await call_next(request)

    if new_session:
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            secure=True,
            samesite="none",
            path="/",
        )

    return response



@app.get("/api/greet")
def greet(request: Request):
    session_id = request.state.session_id
    session_data = session_store.get(session_id, {})
    cb_url = session_data.get("cb_url", "unknown")
    return {"message": f"Hello {cb_url}!"}


@app.get("/api/session_check")
def session_check(request: Request):
    session_id = request.state.session_id
    print(session_id)

    if not session_id or session_id not in session_store:
        raise HTTPException(status_code=400, detail="Session not found")

    cb_api_client = session_store[session_id].get("cb_api_client")

    if not cb_api_client:
        raise HTTPException(status_code=400, detail="Codebeamer client not found")

    return {
        "status": "connected",
        "url": session_store[session_id]["cb_url"]
    }



@app.post("/api/connect")
async def connect(request: Request):
    data = await request.json()
    url = data.get("url")
    username = data.get("username")
    password = data.get("password")
    cb_api_client = CBApiClient(url, username, password)
    session_id = request.state.session_id
    print(session_id)

    if session_id not in session_store:
        session_store[session_id] = {}

        # When creating a new session
        session_store[session_id] = {
            "created_at": time.time(),
        }

    session_store[session_id]["cb_url"] = url
    session_store[session_id]["cb_api_client"] = cb_api_client

    try:
        projects = cb_api_client.project_api_instance.get_projects()
    except ServiceException:
        session_store[session_id]["cb_api_client"] = None
        raise HTTPException(status_code=500, detail="Server Error: Please confirm server is running")
    except UnauthorizedException:
        session_store[session_id]["cb_api_client"] = None
        raise HTTPException(status_code=401, detail="Unauthorized: Please check your username and password")
    except NotFoundException:
        session_store[session_id]["cb_api_client"] = None
        raise HTTPException(status_code=404,
                            detail="The server was not found. Please ensure your URL is pointing to a Codebeamer instance.")
    except Exception as e:
        session_store[session_id]["cb_api_client"] = None
        raise HTTPException(status_code=500, detail=str(e))

    project_map = {project.name: project.id for project in projects}
    session_store[session_id]["project_map"] = project_map
    return {"status": "success"}


@app.post("/api/disconnect")
async def disconnect(request: Request, response: Response):
    session_id = request.state.session_id

    # Delete entire session if it exists
    if session_id in session_store:
        session_store.pop(session_id, None)

    # Clear the cookie on client
    response.delete_cookie("session_id")

    return {"status": "success"}


@app.post("/api/set_product")
async def set_product(request: Request):
    data = await request.json()
    product_name = data.get("product_name")
    session_id = request.state.session_id

    if not session_id or session_id not in session_store:
        raise HTTPException(status_code=400, detail="Session not found")

    session_store[session_id]["product_name"] = product_name


@app.get("/api/project_names")
async def get_project_names(request: Request):
    session_id = request.state.session_id
    if not session_id or session_id not in session_store:
        raise HTTPException(status_code=400, detail="Session not found")

    project_map = session_store[session_id].get("project_map")
    if not project_map:
        raise HTTPException(status_code=404, detail="No project map found")

    return {"project_names": list(project_map.keys())}


@app.post("/api/trackers")
async def get_tracker_names(request: Request):
    data = await request.json()
    project_name = data.get("project_name")
    session_id = request.state.session_id

    if not session_id or session_id not in session_store:
        raise HTTPException(status_code=400, detail="Session not found")

    project_map = session_store[session_id].get("project_map")
    if not project_map or project_name not in project_map:
        raise HTTPException(status_code=404, detail="Project not found")

    project_id = project_map[project_name]
    cb_api_client = session_store[session_id].get("cb_api_client")

    if not cb_api_client:
        raise HTTPException(status_code=400, detail="Codebeamer client not found")

    try:
        trackers = cb_api_client.project_api_instance.get_trackers(project_id)
        tracker_list = [{"name": tracker.name, "id": tracker.id} for tracker in trackers]
        return {"trackers": tracker_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tracker_items")
async def get_tracker_names(request: Request):
    data = await request.json()
    tracker_id = data.get("tracker_id")
    session_id = request.state.session_id

    if not session_id or session_id not in session_store:
        raise HTTPException(status_code=400, detail="Session not found")

    cb_api_client = session_store[session_id].get("cb_api_client")

    if not cb_api_client:
        raise HTTPException(status_code=400, detail="Codebeamer client not found")

    try:
        tracker_items = cb_api_client.get_paginated_tracker_items(int(tracker_id))
        tracker_item_list = [{"name": tracker.name, "id": tracker.id} for tracker in tracker_items][::-1]
        return {"tracker_items": tracker_item_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate_items")
async def generate_items(request: Request):
    data = await request.json()
    requirement_type = data.get("requirement_type")
    tracker_id = data.get("tracker_id")
    item_count = data.get("item_count")
    additional_rules = data.get("additional_rules")

    session_id = request.state.session_id
    print(session_id)
    if not session_id or session_id not in session_store:
        raise HTTPException(status_code=400, detail="Session not found")

    session_data = session_store[session_id]
    cb_api_client = session_data.get("cb_api_client")
    product = session_data.get("product_name")

    if not cb_api_client:
        raise HTTPException(status_code=400, detail="Missing session data")

    if not product:
        raise HTTPException(status_code=400, detail="Product not set")

    try:
        TopLevelItemGenerator(cb_api_client, product, int(tracker_id),
                              item_count, requirement_type, additional_rules).generate()
        return {"status": "success", "message": "Top level items generated"}

    except Exception as e:
        print("Exception occurred:", str(e))
        traceback.print_exc()  # This prints the full traceback to the console
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.post("/api/generate_traceability")
async def generate_traceability(request: Request):
    data = await request.json()
    upstream_tracker_id = data.get("upstream_tracker_id")
    selected_upstream_items = data.get("selected_tracker_items")
    downstream_tracker_id = data.get("downstream_tracker_id")
    downstream_count = data.get("downstream_count")
    additional_rules = data.get("additional_rules")

    session_id = request.state.session_id
    if not session_id or session_id not in session_store:
        raise HTTPException(status_code=400, detail="Session not found")

    session_data = session_store[session_id]
    cb_api_client = session_data.get("cb_api_client")
    product = session_data.get("product_name")

    if not cb_api_client or not product:
        raise HTTPException(status_code=400, detail="Missing session data")

    try:
        TraceabilityGenerator(cb_api_client, product, int(upstream_tracker_id),
                              selected_upstream_items, int(downstream_tracker_id), downstream_count,
                              additional_rules).generate()
        return {"status": "success", "message": "Top level items generated"}

    except Exception as e:
        print("Exception occurred:", str(e))
        traceback.print_exc()  # This prints the full traceback to the console
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.post("/api/delete_tracker_data")
async def delete_tracker_data(request: Request):
    data = await request.json()
    tracker_id = data.get("tracker_id")

    session_id = request.state.session_id

    if not session_id or session_id not in session_store:
        raise HTTPException(status_code=400, detail="Session not found")

    session_data = session_store[session_id]
    cb_api_client = session_data.get("cb_api_client")

    if not cb_api_client:
        raise HTTPException(status_code=400, detail="Missing session data")

    try:
        DeleteAllTrackerData(cb_api_client, int(tracker_id)).generate()
        return {"status": "success", "message": "All tracker items deleted"}

    except Exception as e:
        print("Exception occured:", str(e))
        traceback.print_exc()  # prints the full traceback to the console
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.post("/api/delete_project_data")
async def delete_project_data(request: Request):
    data = await request.json()
    project_name = data.get("project_name")

    session_id = request.state.session_id

    if not session_id or session_id not in session_store:
        raise HTTPException(status_code=400, detail="Session not found")

    project_map = session_store[session_id].get("project_map")
    if not project_map or project_name not in project_map:
        raise HTTPException(status_code=404, detail="Project not found")

    project_id = project_map[project_name]

    session_data = session_store[session_id]
    cb_api_client = session_data.get("cb_api_client")

    if not cb_api_client:
        raise HTTPException(status_code=400, detail="Missing session data")

    try:
        DeleteAllProjectData(cb_api_client, int(project_id)).generate()
        return {"status": "success", "message": "All project data deleted"}

    except Exception as e:
        print("Exception occurred:", str(e))
        traceback.print_exc()  # prints the full traceback to the console
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.post("/api/generate_batch_items")
async def generate_batch_items(request: Request):
    data = await request.json()
    count = data.get("item_count")
    tracker_id = data.get("tracker_id")
    tracker_name = data.get("tracker_name")

    session_id = request.state.session_id

    if (not session_id or session_id not in session_store):
        raise HTTPException(status_code=400, detail="Session not found")

    session_data = session_store[session_id]
    cb_api_clint = session_data.get("cb_api_client")

    if not cb_api_clint:
        raise HTTPException(status_code=400, detail="Missing session data")

    try:
        BatchItemGeneration(cb_api_clint, int(tracker_id), tracker_name, int(count)).generate()
        return {"status": "success", "message": "Batch items generated"}
    except Exception as e:
        print("Exception occurred:", str(e))
        traceback.print_exc()  # prints full traceback to console
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.post("/api/update_item_metadata")
async def update_item_metadata(request: Request):
    data = await request.json()
    tracker_id = data.get("tracker_id")
    item_id_list = data.get("item_id_list")
    project_name = data.get("project_name")

    session_id = request.state.session_id

    if (not session_id or session_id not in session_store):
        raise HTTPException(status_code=400, detail="Session not found")

    project_map = session_store[session_id].get("project_map")
    if not project_map or project_name not in project_map:
        raise HTTPException(status_code=404, detail="Project not found")

    project_id = project_map[project_name]

    session_data = session_store[session_id]
    cb_api_client = session_data.get("cb_api_client")

    if not cb_api_client:
        raise HTTPException(status_code=500, detail="Missing session data")

    try:
        FieldUpdater(cb_api_client, int(tracker_id), int(project_id), item_id_list).generate()
        return {"status": "success", "message": "Item metadata updated successfully"}
    except Exception as e:
        print("Exception occurred:", str(e))
        traceback.print_exc()  # prints traceback to console
        raise HTTPException(status_code=500, detail=f"Internal Error: {str(e)}")


@app.post("/api/update_item_statuses")
async def update_item_statuses(request: Request):
    data = await request.json()
    tracker_id = data.get("tracker_id")
    item_id_list = data.get("item_id_list")

    session_id = request.state.session_id

    if (not session_id or session_id not in session_store):
        raise HTTPException(status_code=400, detail="Session not found")

    session_data = session_store[session_id]
    cb_api_client = session_data.get("cb_api_client")

    if not cb_api_client:
        raise HTTPException(status_code=500, detail="Missing session data")

    try:
        StatusUpdater(cb_api_client, int(tracker_id), item_id_list).generate()
        return {"status": "success", "message": "Item statuses updated successfully"}
    except Exception as e:
        print("Exception occurred:", str(e))
        traceback.print_exc()  # prints full traceback to console
        raise HTTPException(status_code=500, detail=f"Internal Error: {str(e)}")


@app.post("/api/generate_test_steps")
async def generate_test_steps(request: Request):
    data = await request.json()
    tracker_id = data.get("tracker_id")
    item_id_list = data.get("item_id_list")

    session_id = request.state.session_id

    if not session_id or session_id not in session_store:
        raise HTTPException(status_code=400, detail="Session not found")

    session_data = session_store[session_id]
    cb_api_client = session_data.get("cb_api_client")
    product = session_data.get("product_name")

    if not cb_api_client:
        raise HTTPException(status_code=500, detail="Missing session data")

    try:
        TestStepGenerator(cb_api_client, product, int(tracker_id), item_id_list).generate()
        return {"status": "success", "message": "Test Steps generated successfully."}
    except Exception as e:
        print("Exception occurred:", str(e))
        traceback.print_exc()  # prints full traceback to console
        raise HTTPException(status_code=500, detail=f"Internal Error: {str(e)}")
