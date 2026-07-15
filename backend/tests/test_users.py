"""프로필 API 테스트. (API 명세서 1-1 조회 / 1-2 수정)

인증 스텁: 토큰 문자열 = clerk_user_id. 첫 요청 시 자동 가입(get_optional_user).
"""

BASE = "/api/v1/users/me"


def test_get_my_profile_requires_auth_401(client):
    r = client.get(BASE)
    assert r.status_code == 401


def test_get_my_profile_ok_auto_creates_user(client, auth):
    r = client.get(BASE, headers=auth("alice"))
    assert r.status_code == 200
    body = r.json()
    assert body["clerk_user_id"] == "alice"
    assert body["nickname"].startswith("user_")


def test_update_nickname_requires_auth_401(client):
    r = client.patch(BASE, json={"nickname": "새이름"})
    assert r.status_code == 401


def test_update_nickname_ok(client, auth):
    r = client.patch(BASE, json={"nickname": "새이름"}, headers=auth("alice"))
    assert r.status_code == 200
    assert r.json()["nickname"] == "새이름"


def test_update_nickname_duplicate_409(client, auth):
    bob = client.get(BASE, headers=auth("bob")).json()  # bob 자동 가입 → 닉네임 확보
    r = client.patch(BASE, json={"nickname": bob["nickname"]}, headers=auth("alice"))
    assert r.status_code == 409
    assert r.json()["detail"]["code"] == "USER_DUPLICATE_NICKNAME"


def test_update_nickname_too_short_422(client, auth):
    r = client.patch(BASE, json={"nickname": "a"}, headers=auth("alice"))
    assert r.status_code == 422
