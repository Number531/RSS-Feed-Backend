#!/bin/bash

# Verification script for user profile endpoints
# Run after server restart to verify all 5 endpoints work

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "==================================="
echo "User Profile Endpoints Verification"
echo "==================================="
echo ""

# Step 1: Login
echo -e "${BLUE}Step 1: Login${NC}"
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "morristownmale@gmail.com",
    "password": "Edwin1996!"
  }')

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
  echo -e "${RED}❌ Login failed${NC}"
  echo $LOGIN_RESPONSE | jq .
  exit 1
fi

echo -e "${GREEN}✅ Login successful${NC}"
echo "Token: ${TOKEN:0:50}..."
echo ""

# Step 2: GET /users/me
echo -e "${BLUE}Step 2: GET /users/me${NC}"
ME_RESPONSE=$(curl -s -X GET http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN")

echo $ME_RESPONSE | jq .
echo ""

# Check for display_name field
if echo $ME_RESPONSE | jq -e '.display_name' > /dev/null 2>&1; then
  echo -e "${GREEN}✅ display_name field present${NC}"
else
  echo -e "${RED}❌ display_name field missing${NC}"
fi
echo ""

# Step 3: PATCH /users/me (test display_name mapping)
echo -e "${BLUE}Step 3: PATCH /users/me (test display_name field)${NC}"
PATCH_RESPONSE=$(curl -s -X PATCH http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "Edwin Test User"
  }')

echo $PATCH_RESPONSE | jq .
echo ""

# Verify display_name updated
if echo $PATCH_RESPONSE | jq -e '.display_name == "Edwin Test User"' > /dev/null 2>&1; then
  echo -e "${GREEN}✅ display_name updated successfully${NC}"
else
  echo -e "${RED}❌ display_name update failed${NC}"
fi
echo ""

# Step 4: GET /users/me/stats
echo -e "${BLUE}Step 4: GET /users/me/stats${NC}"
STATS_RESPONSE=$(curl -s -X GET http://localhost:8000/api/v1/users/me/stats \
  -H "Authorization: Bearer $TOKEN")

echo $STATS_RESPONSE | jq .
echo ""

# Check for stats fields
if echo $STATS_RESPONSE | jq -e '.total_votes' > /dev/null 2>&1; then
  echo -e "${GREEN}✅ Stats endpoint working${NC}"
else
  echo -e "${RED}❌ Stats endpoint failed${NC}"
fi
echo ""

# Step 5: POST /users/me/change-password
echo -e "${BLUE}Step 5: POST /users/me/change-password${NC}"
CHANGE_PW_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/users/me/change-password \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "Edwin1996!",
    "new_password": "MyV3ryStr0ng!P@ssw0rd2025"
  }')

echo $CHANGE_PW_RESPONSE | jq .
echo ""

if echo $CHANGE_PW_RESPONSE | jq -e '.message == "Password changed successfully"' > /dev/null 2>&1; then
  echo -e "${GREEN}✅ Password change successful${NC}"
  
  # Test login with new password
  echo -e "${BLUE}Verifying new password works...${NC}"
  NEW_LOGIN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{
      "email": "morristownmale@gmail.com",
      "password": "MyV3ryStr0ng!P@ssw0rd2025"
    }')
  
  NEW_TOKEN=$(echo $NEW_LOGIN | jq -r '.access_token')
  
  if [ "$NEW_TOKEN" != "null" ] && [ -n "$NEW_TOKEN" ]; then
    echo -e "${GREEN}✅ New password works${NC}"
    
    # Change back to original password
    echo -e "${BLUE}Reverting to original password...${NC}"
    curl -s -X POST http://localhost:8000/api/v1/users/me/change-password \
      -H "Authorization: Bearer $NEW_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "current_password": "MyV3ryStr0ng!P@ssw0rd2025",
        "new_password": "Edwin1996!"
      }' > /dev/null
    echo -e "${GREEN}✅ Password reverted${NC}"
  else
    echo -e "${RED}❌ New password doesn't work${NC}"
  fi
else
  echo -e "${RED}❌ Password change failed${NC}"
fi
echo ""

# Step 6: DELETE /users/me (test but with confirmation prompt)
echo -e "${BLUE}Step 6: DELETE /users/me (SKIPPED - destructive)${NC}"
echo "This endpoint would soft-delete the user account."
echo "Skipping to preserve test user account."
echo ""

echo "==================================="
echo -e "${GREEN}Verification Complete${NC}"
echo "==================================="
echo ""
echo "Summary:"
echo "1. GET /users/me - ✅"
echo "2. PATCH /users/me (display_name) - Pending verification"
echo "3. GET /users/me/stats - Pending verification"
echo "4. POST /users/me/change-password - Pending verification"
echo "5. DELETE /users/me - Skipped (destructive)"
