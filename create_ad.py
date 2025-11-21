from database import SessionLocal, Ad

async with SessionLocal() as session:
    ad = Ad(
        user_id=message.from_user.id,
        name=data["name"],
        age=data["age"],
        gender=data["gender"],
        about=data["about"],
        target_gender=data["target_gender"],   # ← ДУЖЕ ВАЖЛИВО
        photo_id=data.get("photo"),
        tg_username=data.get("username"),      # ← або None
    )
    session.add(ad)
    await session.commit()
