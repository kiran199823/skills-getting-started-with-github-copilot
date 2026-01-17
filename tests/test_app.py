import pytest


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirects_to_static(self, client):
        """Test that root endpoint redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for getting activities"""
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        # Check that we have all expected activities
        expected_activities = [
            "Basketball Club", "Tennis Club", "Art Club", "Music Ensemble",
            "Debate Club", "Robotics Team", "Chess Club", "Programming Class", "Gym Class"
        ]
        for activity in expected_activities:
            assert activity in data
    
    def test_activities_have_required_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        required_fields = ["description", "schedule", "max_participants", "participants"]
        for activity_name, activity_data in data.items():
            for field in required_fields:
                assert field in activity_data, f"Activity {activity_name} missing field {field}"
    
    def test_activities_have_correct_data_types(self, client):
        """Test that activity data has correct types"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert isinstance(activity_data["description"], str)
            assert isinstance(activity_data["schedule"], str)
            assert isinstance(activity_data["max_participants"], int)
            assert isinstance(activity_data["participants"], list)
    
    def test_basketball_club_initial_state(self, client):
        """Test Basketball Club has expected initial state"""
        response = client.get("/activities")
        data = response.json()
        
        basketball = data["Basketball Club"]
        assert basketball["max_participants"] == 15
        assert "james@mergington.edu" in basketball["participants"]
        assert len(basketball["participants"]) == 1


class TestSignupEndpoint:
    """Tests for signing up to activities"""
    
    def test_signup_valid_activity(self, client):
        """Test signing up for a valid activity"""
        response = client.post(
            "/activities/Basketball%20Club/signup?email=newstudent@mergington.edu",
            follow_redirects=True
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "newstudent@mergington.edu" in data["message"]
    
    def test_signup_adds_participant(self, client):
        """Test that signup actually adds the participant"""
        # Sign up
        client.post(
            "/activities/Basketball%20Club/signup?email=newstudent@mergington.edu"
        )
        
        # Verify participant was added
        response = client.get("/activities")
        data = response.json()
        assert "newstudent@mergington.edu" in data["Basketball Club"]["participants"]
    
    def test_signup_invalid_activity(self, client):
        """Test signing up for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent%20Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_multiple_participants(self, client):
        """Test multiple participants can sign up for same activity"""
        # Sign up first student
        client.post(
            "/activities/Tennis%20Club/signup?email=student1@mergington.edu"
        )
        
        # Sign up second student
        client.post(
            "/activities/Tennis%20Club/signup?email=student2@mergington.edu"
        )
        
        # Verify both are registered
        response = client.get("/activities")
        data = response.json()
        participants = data["Tennis Club"]["participants"]
        assert "student1@mergington.edu" in participants
        assert "student2@mergington.edu" in participants
        assert len(participants) == 3  # sarah + 2 new students


class TestUnregisterEndpoint:
    """Tests for unregistering from activities"""
    
    def test_unregister_existing_participant(self, client):
        """Test unregistering an existing participant"""
        response = client.post(
            "/activities/Basketball%20Club/unregister?email=james@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert "james@mergington.edu" in data["message"]
    
    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes the participant"""
        # Unregister
        client.post(
            "/activities/Basketball%20Club/unregister?email=james@mergington.edu"
        )
        
        # Verify participant was removed
        response = client.get("/activities")
        data = response.json()
        assert "james@mergington.edu" not in data["Basketball Club"]["participants"]
    
    def test_unregister_nonexistent_participant(self, client):
        """Test unregistering a participant not in the activity"""
        response = client.post(
            "/activities/Basketball%20Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Participant not found" in data["detail"]
    
    def test_unregister_invalid_activity(self, client):
        """Test unregistering from non-existent activity"""
        response = client.post(
            "/activities/Nonexistent%20Club/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_unregister_from_activity_with_multiple_participants(self, client):
        """Test unregistering when activity has multiple participants"""
        # Music Ensemble has alex and lucas initially
        response = client.post(
            "/activities/Music%20Ensemble/unregister?email=alex@mergington.edu"
        )
        assert response.status_code == 200
        
        # Verify alex was removed but lucas remains
        response = client.get("/activities")
        data = response.json()
        participants = data["Music Ensemble"]["participants"]
        assert "alex@mergington.edu" not in participants
        assert "lucas@mergington.edu" in participants


class TestIntegration:
    """Integration tests combining multiple endpoints"""
    
    def test_signup_then_unregister(self, client):
        """Test signing up and then unregistering"""
        email = "testuser@mergington.edu"
        activity = "Chess%20Club"
        
        # Sign up
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        
        # Verify signed up
        response = client.get("/activities")
        data = response.json()
        assert email in data["Chess Club"]["participants"]
        
        # Unregister
        response = client.post(f"/activities/{activity}/unregister?email={email}")
        assert response.status_code == 200
        
        # Verify unregistered
        response = client.get("/activities")
        data = response.json()
        assert email not in data["Chess Club"]["participants"]
    
    def test_signup_and_unregister_participant_count(self, client):
        """Test that participant count updates correctly"""
        email = "counttest@mergington.edu"
        activity = "Art%20Club"
        
        # Get initial count
        response = client.get("/activities")
        initial_count = len(response.json()["Art Club"]["participants"])
        
        # Sign up
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Check count increased
        response = client.get("/activities")
        assert len(response.json()["Art Club"]["participants"]) == initial_count + 1
        
        # Unregister
        client.post(f"/activities/{activity}/unregister?email={email}")
        
        # Check count back to initial
        response = client.get("/activities")
        assert len(response.json()["Art Club"]["participants"]) == initial_count
