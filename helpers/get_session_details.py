import requests

def get_session_details(session_id: str, user_id: str):
    try:
        response = requests.get(
            f"http://localhost:3000/api/sessions/data",
            params={"id": session_id},
            headers={"Authorization": user_id},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        session = data.get("session")
        
        if not session:
            raise ValueError(f"Session not found for session_id: {session_id}")
        
        return session
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to get session details: {e}")
        raise
    except ValueError as e:
        print(f"[ERROR] {e}")
        raise