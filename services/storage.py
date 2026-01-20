import json
from datetime import datetime
from typing import Optional, Dict
import streamlit as st

class StorageService:
    """
    Gestion du stockage sans base de données.
    Utilise st.session_state + export/import JSON.
    """

    @staticmethod
    def save_to_session(key: str, data: any) -> None:
        """Sauvegarde dans la session Streamlit"""
        st.session_state[key] = data

    @staticmethod
    def get_from_session(key: str, default=None) -> any:
        """Récupère depuis la session"""
        return st.session_state.get(key, default)

    @staticmethod
    def export_to_json(data: dict) -> str:
        """
        Génère un JSON téléchargeable.
        Retourne le contenu JSON formaté.
        """
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "version": "1.0",
            "data": data
        }
        return json.dumps(export_data, ensure_ascii=False, indent=2, default=str)

    @staticmethod
    def import_from_json(json_content: str) -> Optional[dict]:
        """
        Parse un JSON importé.
        Valide la structure et retourne les données.
        """
        try:
            parsed = json.loads(json_content)
            if "data" in parsed:
                return parsed["data"]
            return parsed
        except json.JSONDecodeError:
            return None
