from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.schemas import schemas
from app.services.llm.llm_manager import LLMManager

router = APIRouter()

@router.get("/settings", response_model=schemas.LLMSettingList)
def get_llm_settings(db: Session = Depends(get_db)):
    """
    Получение списка настроек ЛЛМ
    """
    llm_manager = LLMManager()
    settings = llm_manager.get_llm_settings()
    return {"settings": settings}

@router.post("/settings", response_model=schemas.LLMSetting)
def add_llm_setting(
    setting: schemas.LLMSettingCreate = Body(...),
    db: Session = Depends(get_db)
):
    """
    Добавление настроек ЛЛМ
    """
    llm_manager = LLMManager()
    try:
        result = llm_manager.add_llm_setting(
            provider=setting.provider,
            model_name=setting.model_name,
            api_key=setting.api_key,
            endpoint_url=setting.endpoint_url,
            is_active=setting.is_active,
            priority=setting.priority
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/settings/{setting_id}", response_model=schemas.LLMSetting)
def update_llm_setting(
    setting_id: int,
    setting: schemas.LLMSettingCreate = Body(...),
    db: Session = Depends(get_db)
):
    """
    Обновление настроек ЛЛМ
    """
    llm_manager = LLMManager()
    try:
        result = llm_manager.update_llm_setting(
            setting_id=setting_id,
            provider=setting.provider,
            model_name=setting.model_name,
            api_key=setting.api_key,
            endpoint_url=setting.endpoint_url,
            is_active=setting.is_active,
            priority=setting.priority
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/settings/{setting_id}")
def delete_llm_setting(setting_id: int, db: Session = Depends(get_db)):
    """
    Удаление настроек ЛЛМ
    """
    llm_manager = LLMManager()
    try:
        result = llm_manager.delete_llm_setting(setting_id=setting_id)
        if result:
            return {"message": f"LLM setting with ID {setting_id} deleted successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to delete LLM setting")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/test-connection")
def test_llm_connection(setting_id: Optional[int] = None, db: Session = Depends(get_db)):
    """
    Тестирование подключения к ЛЛМ
    """
    llm_manager = LLMManager()
    result = llm_manager.test_llm_connection(setting_id=setting_id)
    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=400, detail=result["message"])

@router.post("/categorize")
def categorize_event(
    event_name: str,
    event_description: str,
    event_organizer: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Категоризация события
    """
    llm_manager = LLMManager()
    try:
        category = llm_manager.categorize_event(
            event_name=event_name,
            event_description=event_description,
            event_organizer=event_organizer
        )
        return {"category": category}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/summarize")
def summarize_event(
    event_name: str,
    event_description: str,
    event_date: str,
    event_location: str,
    event_organizer: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Создание краткого резюме события
    """
    llm_manager = LLMManager()
    try:
        summary = llm_manager.summarize_event(
            event_name=event_name,
            event_description=event_description,
            event_date=event_date,
            event_location=event_location,
            event_organizer=event_organizer
        )
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
