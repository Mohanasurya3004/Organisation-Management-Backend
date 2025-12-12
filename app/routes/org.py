from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from passlib.context import CryptContext
from app.database import get_db
from app.auth import get_current_admin
from fastapi import Depends

router = APIRouter(prefix="/org", tags=["Organization"])

pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")



class CreateOrgRequest(BaseModel):
    organization_name: str
    email: str
    password: str

class UpdateOrgRequest(BaseModel):
    organization_name: str
    email: str
    password: str


def hash_password(password: str):
    return pwd_context.hash(password)


@router.post("/create")
def create_organization(data: CreateOrgRequest):
    try:
        db = get_db()
        organizations = db["organizations"]
        admins = db["admins"]

        org_name = data.organization_name.lower()

        if organizations.find_one({"organization_name": org_name}):
            raise HTTPException(status_code=400, detail="Organization already exists")

        admin_result = admins.insert_one({
            "email": data.email,
            "password": hash_password(data.password),
            "organization": org_name
        })

        organizations.insert_one({
            "organization_name": org_name,
            "collection_name": f"org_{org_name}",
            "admin_id": str(admin_result.inserted_id)
        })

        return {
            "message": "Organization created successfully",
            "organization": org_name
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/update")
def update_organization(
    data: UpdateOrgRequest,
    current_admin: dict = Depends(get_current_admin)
):
    db = get_db()
    organizations = db["organizations"]
    admins = db["admins"]

    old_org = current_admin["organization"]
    new_org = data.organization_name.lower()

    # 1. Validate new org name does not already exist
    if organizations.find_one({"organization_name": new_org}):
        raise HTTPException(
            status_code=400,
            detail="Organization name already exists"
        )

    old_collection = f"org_{old_org}"
    new_collection = f"org_{new_org}"

    # 2. Create new collection and copy data
    if old_collection in db.list_collection_names():
        old_data = list(db[old_collection].find({}, {"_id": 0}))

        if old_data:
            db[new_collection].insert_many(old_data)

        # 3. Drop old collection
        db.drop_collection(old_collection)

    # 4. Update organization metadata
    organizations.update_one(
        {"organization_name": old_org},
        {"$set": {
            "organization_name": new_org,
            "collection_name": new_collection
        }}
    )

    # 5. Update admin credentials
    admins.update_many(
        {"organization": old_org},
        {"$set": {
            "organization": new_org,
            "email": data.email,
            "password": hash_password(data.password)
        }}
    )

    return {
        "message": "Organization updated successfully",
        "old_organization": old_org,
        "new_organization": new_org
    }

@router.delete("/delete")
def delete_organization(
    current_admin: dict = Depends(get_current_admin)
):
    db = get_db()
    organizations = db["organizations"]
    admins = db["admins"]

    org_name = current_admin["organization"]
    org_collection = f"org_{org_name}"

    # Delete org metadata
    organizations.delete_one({"organization_name": org_name})

    # Delete admin(s)
    admins.delete_many({"organization": org_name})

    # Delete org-specific collection
    db.drop_collection(org_collection)

    return {
        "message": f"Organization '{org_name}' deleted successfully"
    }
