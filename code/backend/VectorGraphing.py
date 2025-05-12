import matplotlib
matplotlib.use('Agg')

import numpy as np
import matplotlib.pyplot as pltgit log --oneline
import math
import io
import base64
from flask import jsonify
from matplotlib.patches import Arc

# This function calculates a side using the Law of Cosines
def laws_of_cosine_side(b, c, A):
    A = np.radians(A)
    return np.sqrt(b**2 + c**2 - 2 * b * c * np.cos(A))

# This function calculates an angle using the Law of Cosines
def laws_of_cosine_angle(a, b, c):
    denominator = 2 * b * c
    if denominator == 0:
        return np.nan  #avoid division by zero
    return np.degrees(np.arccos(np.clip((b**2 + c**2 - a**2) / denominator, -1, 1)))

def Display_Vector(lead1, lead3):
    angles = np.radians([0, 60, 120])
    axes_vectors = np.array([[np.cos(a), np.sin(a)] for a in angles])

    k = 4
    
    # Set up the plot
    fig, ax = plt.subplots(figsize=(k+2, k+2))
    ax.set_xlim(-k, k)
    ax.set_ylim(-k, k)
    
    ax.set_aspect('equal')
    
    leads_labels = [[1,2],[3,4],[5,6]]
    index = 0
    
    for vec in axes_vectors:
        ax.plot([-k * vec[0], k * vec[0]], [-k * vec[1], k * vec[1]], 'k-', linewidth=1)  # Extended axes
        leads_labels[index][0] = k *vec[0]
        leads_labels[index][1] = k *vec[1]
        index = index + 1
        
    #Labels each leads on the triaxial
    
    ax.text(leads_labels[0][0],leads_labels[0][1], "Lead I", color="black", fontsize=12, verticalalignment='bottom')
    ax.text(leads_labels[1][0],leads_labels[1][1]+0.5, "Lead III", color="black", fontsize=12, verticalalignment='bottom')
    ax.text(leads_labels[2][0] - 0.5,leads_labels[2][1] + 0.5, "Lead II", color="black", fontsize=12, verticalalignment='bottom')
   
    ax.text(leads_labels[0][0],leads_labels[0][1] - 0.5, "+0", color="black", fontsize=12, verticalalignment='bottom')
    
    ax.text(leads_labels[1][0],leads_labels[1][1], "-60", color="black", fontsize=12, verticalalignment='bottom')
    ax.text(leads_labels[2][0] - 0.5,leads_labels[2][1], "-120", color="black", fontsize=12, verticalalignment='bottom')
    
    ax.text(-leads_labels[1][0] - 0.3,-leads_labels[1][1] - 0.5, "+120", color="black", fontsize=12, verticalalignment='bottom')
    ax.text(-(leads_labels[2][0] + 0.2),-leads_labels[2][1]-0.5, "+60", color="black", fontsize=12, verticalalignment='bottom')
    
    
    v1 = np.array([lead1, 0])  # Along the x-axis (lead 1)
    v3 = np.dot(axes_vectors[1], -lead3)  # Along the 60° axis  (lead 3)
    
    D = 120
   
    DC = np.absolute(lead1)
    DA = np.absolute(lead3)


    AC = laws_of_cosine_side(DC,DA,D)
    C2 = laws_of_cosine_angle(DA,DC,AC)
    A1 = laws_of_cosine_angle(DC,DA,AC)

    C1 = A1
    A2 = C2
    A = A1 + A2
    
    DB = laws_of_cosine_side(DA,DC,A)
    D1 = laws_of_cosine_angle(DA,DC,DB)
    D2 = laws_of_cosine_angle(DC,DA,DB)
    B2 = D2

    AB = laws_of_cosine_side(DA, DB, D2) #AB must be same as DC
    BC = laws_of_cosine_side(DC, DB, D1) #BC is the same as DA
    
    #Solve the entire parallelogram to ensure accuracy according to the sponsor
    
    B1 = D1
    E2 = 180 - A1 - D2
    E4 = E2
    E1 = 180 - C2 - D1
    E3 = E1
    
    E = E1 + E2 + E3 + E4
    
    #If E == 360 then the calculation for the parallelogram is complete and correct
    
    Magnitude_result = 0
    Angle_result = 0
    
    if lead1 > 0 and lead3 > 0:
        Magnitude_result = DB
        Angle_result = D1
        
    elif lead1 > 0 and lead3  < 0:
        Magnitude_result = AC
        Angle_result = -(A2)
       
    elif lead1 < 0 and lead3  > 0:
        Magnitude_result = AC
        Angle_result = C1 + 120
        
    elif lead1 < 0 and lead3  < 0:
        Magnitude_result = DB
        Angle_result = -(B2 + 60)
       
    Angle_result = math.ceil(Angle_result-0.5)
    
    diagnose = "ERROR"
    
    if Angle_result >= -29.0 and Angle_result <= 80.0:
        diagnose = "No Axis Deviation"
        
    elif Angle_result <= -30.0 and Angle_result >= -80.0:
        diagnose = "Abnormal Left Axis Deviation"
        
    elif Angle_result <= -100.0 and Angle_result >= -180.0:
        diagnose = "Extreme Axis Deviation"
        
    elif Angle_result >= 100.0 and Angle_result <= 180.0:
        diagnose = "Abnormal Right Axis Deviation"
        
    elif Angle_result <= -81.0 and Angle_result >= -99.0:
        diagnose = "Superior Axis Deviation"
        
    elif Angle_result >= 81.0 and Angle_result <= 99.0:
        diagnose = "Inferior Axis Deviation"

    #EAX = Electrical Axis Deviation
    EAX_Area_Shading = ([-30,80],[-80,-30],[100,180],[-100,-180],[-100,-80],[80,100])
    num_EAX = len(EAX_Area_Shading)
    
    radius = k
    colors = ('skyblue','red','yellow','purple','green','orange')
    
    for i in range(num_EAX):
            
        theta = np.linspace(-np.radians(EAX_Area_Shading[i][0]), -np.radians(EAX_Area_Shading[i][1]))
         
        # Convert polar coordinates to Cartesian (x, y)
        x = radius * np.cos(theta)
        y = radius * np.sin(theta)

        # Fill the area between the two radius values
        ax.fill(np.append(x, 0), np.append(y, 0), color=colors[i], alpha=0.5)
    
    #Adding angles indicator for each EAX
    EAX_angles = np.radians([30, 80, 100, -100,-80])  # Convert degrees to radians
    EAX_vectors = np.array([[np.cos(a), np.sin(a)] for a in EAX_angles])  # Unit vectors

    EAX_labels = [[1,1],[2,2],[3,3],[4,4],[5,5]]
    index_2 = 0
    for vec in EAX_vectors:
        EAX_labels[index_2][0] = k *vec[0]
        EAX_labels[index_2][1] = k *vec[1]
        index_2 = index_2 + 1
        
    ax.text(EAX_labels[0][0],EAX_labels[0][1], "-30", color="black", fontsize=12, verticalalignment='bottom')
    ax.text(EAX_labels[1][0],EAX_labels[1][1] + 0.1, "-80", color="black", fontsize=12, verticalalignment='bottom')
    ax.text(EAX_labels[2][0] - 0.2,EAX_labels[2][1] + 0.1, "-100", color="black", fontsize=12, verticalalignment='bottom')
    ax.text(EAX_labels[3][0] - 0.2,EAX_labels[3][1] - 0.5, "100", color="black", fontsize=12, verticalalignment='bottom')
    ax.text(EAX_labels[4][0],EAX_labels[4][1] - 0.5, "80", color="black", fontsize=12, verticalalignment='bottom')
    
    v_sum = v1 + v3
    Vector_scaling = 2
    ax.quiver(0, 0, v_sum[0] * Vector_scaling, v_sum[1] * Vector_scaling, color='black', angles='xy', scale_units='xy', scale=1)
    
    #Displaying the angle between the result vector and Lead 1
    if (Angle_result >=0):
        arc = Arc((0,0), Magnitude_result, Magnitude_result, angle=0, theta1=-Angle_result, theta2=0, color='black')
        plt.gca().add_patch(arc)
    else:
        arc = Arc((0,0), Magnitude_result, Magnitude_result, angle=0, theta1=0, theta2=-Angle_result, color='black')
        plt.gca().add_patch(arc)
    
    # Display magnitude,angle and diagnose
    #Label for magnitude of the result vector
    ax.text(-1.3-k,0.2-k,"Magnitude: ",color="black", fontsize=12, verticalalignment='bottom')
    ax.text(0.6-k,0.2-k,round(Magnitude_result,2),color="black", fontsize=12, verticalalignment='bottom')
    
    #Label for the angle of the result vector
    ax.text(-1.3-k, -0.3-k,"Angle        : ",color="black", fontsize=12, verticalalignment='bottom')  
    ax.text(0.6-k,-0.3-k,round(Angle_result,2),color="black", fontsize=12, verticalalignment='bottom')
        
    #Label for diagnose 
    ax.text(-1.3-k,-0.8-k,"Diagnose  : ",color="black", fontsize=12, verticalalignment='bottom')
    ax.text(0.6-k,-0.8-k,diagnose,color="black", fontsize=12, verticalalignment='bottom')
    
    #Label For the Unit Scale
    ax.text(0.5,-0.35, "0.5", color="black", fontsize=k+8, verticalalignment='bottom')
    
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_frame_on(False)
    
    #Labeling ticks on the triaxial coordinate system
    for i, vec in enumerate(axes_vectors):
        for j in range(1, 5):  # Adding markers at multiples of 1
            # Create points along the axis at regular intervals
            line_x = vec[0] * j
            line_y = vec[1] * j

            # Create a small perpendicular segment to simulate a "marker"
            dx, dy = -0.1 * vec[1], 0.1 * vec[0]  # Rotate 90 degrees
            ax.plot([line_x - dx, line_x + dx], [line_y - dy, line_y + dy], color='black', linewidth=1)
            ax.plot([-line_x - dx, -line_x + dx], [-line_y - dy, -line_y + dy], color='black', linewidth=1)
    
    img_io = io.BytesIO()
    fig.savefig(img_io, format='png', bbox_inches='tight')
    img_io.seek(0) 

    plt.close(fig)

    # Convert image to Base64 and return JSON
    base64_img = base64.b64encode(img_io.getvalue()).decode('utf-8')
    return jsonify({"image": base64_img, "magnitude": Magnitude_result, "angle": Angle_result, 
        "side_AB": float(AB), #return all sides
        "side_DC": float(DC),
        "side_AD": float(DA),
        "side_BC": float(BC),
        "angle_A": float(A1 + A2), #return all angles
        "angle_B": float(B1 + B2),
        "angle_C": float(C1 + C2),
        "angle_D": float(D1 + D2),
        "E": float(E)
    })

if __name__ == '__main__':
    Display_Vector(3, 2)

