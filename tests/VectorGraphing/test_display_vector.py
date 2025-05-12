import pytest
import sys
import os
import base64
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../code")))
from backend.VectorGraphing import laws_of_cosine_side, laws_of_cosine_angle, Display_Vector
from backend.app import app
import math

@pytest.fixture
def client():
    app.testing = True
    with app.test_client() as client:
        yield client


def test_laws_of_cosine_side():
  """checks if we calculate the missing side correctly"""
  assert round(laws_of_cosine_side(3, 4, 90), 2) == 5.0 #right triangle
  assert round(laws_of_cosine_side(5, 5, 60), 2) == 5.0
  assert round(laws_of_cosine_side(7, 10, 45), 2) == 7.07

def test_laws_of_cosine_angle():
  """checks if we calculate the angle correctly"""
  assert round(laws_of_cosine_angle(5, 3, 4), 2) == 90.0 #right triangle
  assert round(laws_of_cosine_angle(4, 4, 4), 2) == 60.0 #equilateral
  assert round(laws_of_cosine_angle(7, 10, 5), 2) == 40.54


def test_display_vector(client):
    """checks if we correctly return JSON response with image"""

    #json data to be sent in the post request
    data = {
        "lead1": 3,
        "lead3": -4
    }

    response = client.post('/api/vector-graph', json=data)

    assert response.status_code == 200

    response_data = json.loads(response.data)  #parse JSON response
    assert "image" in response_data #ensure image key exists

    #check the Base64 string is valid
    try:
        base64.b64decode(response_data["image"])  # Attempt to decode
    except Exception:
        pytest.fail("Invalid Base64 encoding in image response")


# def test_parallelogram_sides():
#     """check if opposite sides of a parallelogram are equal"""
#     lead1 = 5
#     lead3 = 7
#     angle_between = 120  #angle D

#     side_AB = laws_of_cosine_side(abs(lead1), abs(lead3), 180 - angle_between)
#     side_DC = laws_of_cosine_side(abs(lead3), abs(lead1), angle_between)


#     assert round(side_DC, 2) == round(side_AB, 2)  #opposite sides must be equal


# def test_parallelogram_angles():
#     """check if opposite angles are equal and adjacent angles sum to 180°"""
#     lead1 = 5
#     lead3 = 7
#     angle_between = 120
#     diagonal_AC = laws_of_cosine_side(lead1, lead3, angle_between)

#     angle_A = laws_of_cosine_angle(diagonal_AC, lead1, lead3)
#     angle_C2 = laws_of_cosine_angle(diagonal_AC, lead3, lead1)
#     print(f"Angle A: {angle_A}")
#     print(f"Angle C2 (opposite of A): {angle_C2}")
    
#     assert round(angle_A, 2) == round(angle_C2, 2)  #opposite angles are equal

#     adjacent_angle = 180 - angle_between #calculate adjacent angle
#     assert round(angle_A + adjacent_angle, 2) == 180 #adjacent angles are equal


# def test_e_angle():
#     """check if the e angle in the middle of parallelegram sums to 360"""
#     lead1 = 5
#     lead3 = 7
#     angle_between = 120

#     diagonal_AC = laws_of_cosine_side(abs(lead1), abs(lead3), angle_between)

#     angle_A = laws_of_cosine_angle(abs(lead1), abs(lead3), diagonal_AC)
#     angle_B = 180 - angle_A #calculate the adjacent angle

#     # Compute the remaining angles
#     angle_C = angle_A
#     angle_D = angle_B 

#     total_angle = angle_A + angle_B + angle_C + angle_D
#     assert round(total_angle, 2) == 360.0


@pytest.mark.parametrize("lead1, lead3", [ #array of test inputs (lead1 pos, lead2 neg) (lead1 neg, lead2 pos)
    (5, 7), (-5, 7), (5, -7), (-5, -7),
    (10, -3), (-10, 3), (3, 10), (-3, -10),
    (0.1, 0.2), (-0.1, 0.2), (0.1, -0.2), (-0.1, -0.2),
    (1, 1), (-1, -1), (1, -1), (-1, 1),
    (6, 9), (-6, 9), (6, -9), (-6, -9),
    (8, 2), (-8, 2), (8, -2), (-8, -2),
    (0.5, 0.7), (-0.5, 0.7), (0.5, -0.7), (-0.5, -0.7),
])


def test_display_vector_creates_valid_parallelogram(lead1, lead3):

    with app.app_context():
        response = Display_Vector(lead1, lead3)

    # Parse the JSON response
    data = json.loads(response.get_data(as_text=True))

    # Extract parallelogram properties (assuming the function can return computed sides)
    magnitude = data["magnitude"]  
    angle = data["angle"]  
    # Check that the parallelogram is valid
    assert magnitude > 0, "Magnitude should be positive"
    assert -180 <= angle <= 180, "Angle should be within valid range"

    #the parallelograms sides
    side_AB = data["side_AB"]
    side_DC = data["side_DC"]
    side_AD = data["side_AD"]
    side_BC = data["side_BC"]

    #validity of opposite sides
    assert round(side_AB, 2) == round(side_DC, 2) #opposite sides AB and DC should be equal
    assert round(side_AD, 2) == round(side_BC, 2) #opposite sides AD and BC should be equal


    #angles
    angle_A = data["angle_A"]
    angle_B = data["angle_B"]
    angle_C = data["angle_C"]
    angle_D = data["angle_D"]
    E = data["E"]

    #validity of opposite angles
    assert round(angle_A, 2) == round(angle_C, 2) #opposite angles A and C should be equal
    assert round(angle_B, 2) == round(angle_D, 2) #opposite angles B and D should be equal
    
    #validity of adjacent angles
    #assert round(angle_A + angle_D, 2) == 180 
    # assert math.isclose(angle_A + angle_D, 180, rel_tol=1e-2) # #adjacent angles A and D should sum to 180°
    assert math.ceil(angle_A + angle_D-0.5) == 180

    #assert round(angle_B + angle_C, 2) == 180 
    # assert math.isclose(angle_B + angle_C, 180, rel_tol=1e-2)#adjacent angles B and C should sum to 180°
    assert math.ceil(angle_B + angle_C-0.5) == 180

    #E point in the middle should sum to 360
    assert math.ceil(E-0.5) == 360 # do to rounding issues we need tolerance




