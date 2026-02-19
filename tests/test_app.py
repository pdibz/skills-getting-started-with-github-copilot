"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original state
    original_activities = {
        k: {**v, "participants": v["participants"].copy()}
        for k, v in activities.items()
    }
    yield
    # Restore original state after test
    for key in activities:
        activities[key]["participants"] = original_activities[key]["participants"].copy()


class TestGetActivities:
    """Tests for retrieving activities"""

    def test_get_activities(self, client, reset_activities):
        """Test that the /activities endpoint returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        assert "Basketball Team" in data
        assert "Tennis Club" in data

    def test_activity_structure(self, client, reset_activities):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        data = response.json()
        activity = data["Basketball Team"]
        
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)


class TestSignup:
    """Tests for student signup functionality"""

    def test_signup_success(self, client, reset_activities):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Basketball Team/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "newstudent@mergington.edu" in activities["Basketball Team"]["participants"]

    def test_signup_duplicate_student(self, client, reset_activities):
        """Test that a student cannot sign up twice for the same activity"""
        email = "alex@mergington.edu"
        response = client.post(
            f"/activities/Basketball Team/signup?email={email}"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_nonexistent_activity(self, client, reset_activities):
        """Test signup for an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_multiple_activities(self, client, reset_activities):
        """Test that a student can sign up for multiple activities"""
        email = "multiactivity@mergington.edu"
        
        response1 = client.post(
            f"/activities/Basketball Team/signup?email={email}"
        )
        assert response1.status_code == 200
        
        response2 = client.post(
            f"/activities/Tennis Club/signup?email={email}"
        )
        assert response2.status_code == 200
        
        assert email in activities["Basketball Team"]["participants"]
        assert email in activities["Tennis Club"]["participants"]


class TestRemoveParticipant:
    """Tests for removing participants from activities"""

    def test_remove_participant_success(self, client, reset_activities):
        """Test successful removal of a participant"""
        email = "alex@mergington.edu"
        assert email in activities["Basketball Team"]["participants"]
        
        response = client.delete(
            f"/activities/Basketball Team/remove?email={email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Removed" in data["message"]
        assert email not in activities["Basketball Team"]["participants"]

    def test_remove_nonexistent_activity(self, client, reset_activities):
        """Test removing from a nonexistent activity"""
        response = client.delete(
            "/activities/Nonexistent Activity/remove?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_remove_not_signed_up_participant(self, client, reset_activities):
        """Test removing a participant who is not signed up"""
        response = client.delete(
            "/activities/Basketball Team/remove?email=notstudent@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]

    def test_remove_then_signup_again(self, client, reset_activities):
        """Test that a removed participant can sign up again"""
        email = "testuser@mergington.edu"
        activity = "Drama Club"
        
        # Sign up
        response1 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response1.status_code == 200
        assert email in activities[activity]["participants"]
        
        # Remove
        response2 = client.delete(f"/activities/{activity}/remove?email={email}")
        assert response2.status_code == 200
        assert email not in activities[activity]["participants"]
        
        # Sign up again
        response3 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response3.status_code == 200
        assert email in activities[activity]["participants"]


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirect(self, client):
        """Test that root endpoint redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
