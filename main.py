from flask import Flask, request
import anastruct
from anastruct import SystemElements, LoadCase, LoadCombination
import numpy as np
import math

app = Flask(__name__)

# Below is a simple hello world to see how quickly a massive set of calculations could be sent from and returned to Inkslinger.
# Code must be put inside "app.route" to run on server
# TODO: Define arguments list as inputs

@app.route('/')
def hello():
    '''
    TODO: Encrypt/Decrypt data as it is passed

    All measurements received in ft, except OC spacing is in inches
    All error handling on string formatting will be done in Inkslinger
    i.e. blank values, characters instead of integers, Spans not adding up to total rake length, etc.
    Longer term, a lot of these checks will be done directly in the eAudit software to guarantee we get good input data

    Inputs from Inkslinger are:
    '''

    '''
    # Dummy data for testing

    # Get data from arguments string. Defaults are defined for testing
    racking = request.args.get('racking','FM') # flush mount or tilt kit
    comp_beneath_PV = bool(request.args.get('compPV','False')) # true if area under PV is re-roofed to shingle, defaults to uniform roof loading
    roof_type = request.args.get('rooftype','shingle') # tile, shingle, or metal
    member_EAI = request.args.get('memberEAI','1600000,5.25,8.25') # Member E, A, and I values in a string format.
    list_EAI = member.EAI.split(",") # Split these guys 
    member_type = request.args.get('membertype','rafter') # truss, rafter, TJI
    member_spacing = float(request.args.get('memberspacing','24'))
    deg_pitch = float(request.args.get('pitch','26')) # pitch of roof in degrees (0-45)
    is_vaulted = bool(request.args.get('vaulted','False')) # check if member is vaulted, defaults to false
    roof_height = float(request.args.get('roofheight','1')) # height of roof in stories (1, 1.5, 2, 3)
    mod_locations_str = request.args.get('modLocations','15,10,8,6,5,3') #Mod locations come in as string
    e2r_mod_locations = mod_locations_str.split(",") # Splits string into a list
    span_locations_str = request.args.get('spanLocations','1.5,5,10,8.5') #Spans come in as string
    spans = span_locations_str.split(",") # Splits string into a list    
    eave_to_ridge = float(request.args.get('etor','25')) # ridge to eave measurement input by design  
    ground_snow_load = float(request.args.get('snow','10')) # snow load input
    wind_load = float(request.args.get('wind','16')) # wind load input
    
    # Dummy data for testing
    racking = "FM"
    comp_beneath_PV = False
    roof_type = "shingle"
    member_size = "2x4"
    true_cut_member = False
    member_type = "rafter"
    member_spacing = float(24)
    deg_pitch = float(26)
    is_vaulted = False
    roof_height = 18 # Data should be ft

    member_EAI = '1400000,5.25,5.36' # Member E, A, and I values in a string format.
    list_EAI = member_EAI.split(",") # Split these guys 

    mod_locations_str = "9,3"
    e2r_mod_locations = mod_locations_str.split(",")

    span_locations_str = "0,12"
    spans = span_locations_str.split(",")

    eave_to_ridge = float(12)
    ground_snow_load = float(10)
    wind_load = float(16)
    '''    
    
    # Get data from arguments string. Defaults are defined for testing
    racking = request.args.get('racking','') # flush mount or tilt kit
    comp_beneath_PV_import = request.args.get('compPV','') # true if area under PV is re-roofed to shingle, defaults to uniform roof loading
    roof_type = request.args.get('rooftype','') # tile, shingle, or metal
    member_type = request.args.get('membertype','') # truss, rafter, TJI
    member_spacing = float(request.args.get('memberspacing',''))
   
    # is_vaulted_import = request.args.get('vaulted','') # check if member is vaulted, defaults to false
    roof_height = float(request.args.get('roofheight','')) # height of roof in stories (1, 1.5, 2, 3)

    member_EAI = request.args.get('memberEAI','') # Member E, A, and I values in a string format.
    list_EAI = member_EAI.split(",") # Split these guys 
    
    eave_to_ridge = float(request.args.get('etor','')) # eave to ridge measurement input by design  

    mod_locations_str = request.args.get('modLocations','') #Mod locations come in as string, largest to smallest
    mod_locations = mod_locations_str.split(",") # Splits string into a list

    span_locations_str = request.args.get('spanLocations','') #Spans come in as string
    spans = span_locations_str.split(",") # Splits string into a list  

    deg_pitch = float(request.args.get('pitch','')) # pitch of roof in degrees (0-45)

    wind_load_str = request.args.get('wind','16,16') # wind load input
    wind_pressures = wind_load_str.split(",") # Splits the string into a list

    nonPV_LL = float(request.args.get('live','20')) # live load input

    snow_string = request.args.get('snow','') # snow load input
    snow = snow_string.split(",")

    # Convert units of inputs to corresponding units used in anastruct

    # Split and convert all mod location values to meters
    # 1 ft = 0.3048 meters
    for i in range(0,len(mod_locations)):
        mod_locations[i] = float(mod_locations[i])*0.3048
    mod_locations.sort()
    for i in range(0,len(spans)):
        spans[i] = float(spans[i])*0.3048
    eave_to_ridge = eave_to_ridge*0.3048
    member_spacing = (member_spacing/12)*0.3048

    #Convert snow to floats
    for i in range(0,2):
        snow[i] = float(snow[i])
        
    # Degrees to radians conversion
    pitch = np.deg2rad(deg_pitch)

    # Wind Load Grab
    wind_load = float(wind_pressures[0])
    wind_up = float(wind_pressures[1])*0.6

    '''
    anaStruct creates structures by adding elements, placing a node between each element.
    The elements when constructed in a line results in a continuous linear analysis of the beam.
    Beam is constructed at the actual pitch so that we can use Localized and Global Y Directions for loading.
    The following section uses the information input by designers to construct the arrays to build the elements of the structure.
    '''
    # Populate array so that elements are ordered and can be properly referenced.

    # Translate spans into support locations
    support_locations = []

    for i in range(0,len(spans)):
        if i==0:
            support_locations.append(spans[i])
        else:
            support_locations.append(spans[i] + support_locations[i-1])

    # Combine Supports list and PV Locations lists
    rafter_array= support_locations + mod_locations

    # Sort list into a constructable object.
    rafter_array.sort()

    # Split each element in half so that we can gather a more accurate deflection value
    final_node_count = len(rafter_array) + (len(rafter_array)-1)
    for i in range (0,(len(rafter_array)-1)):
        rafter_array.insert(i+(i+1),(rafter_array[i+i]+rafter_array[i+i+1])/2)

    # Use sine and cosine to convert the horizontal dimensions into pitched x and y coordinates
    # Create an additional array to distinguish coordinates where arrays and supports are
    tmp_member_coordinates = [[i*np.cos(pitch),i*np.sin(pitch)] for i in rafter_array]
    support_coordinates = [[i*np.cos(pitch),i*np.sin(pitch)] for i in support_locations]
    mod_coordinates = [[i*np.cos(pitch),i*np.sin(pitch)] for i in mod_locations]

    # Add origin point to coordinates
    tmp_member_coordinates.insert(0,[0,0])

    # Clear out any repeated coordinate values, so we don't spit out zero length elements
    member_coordinates = []
    for i in tmp_member_coordinates:
        if i not in member_coordinates:
            member_coordinates.append(i)
        else:
            pass

    '''
    Instantiate System Elements object.
    Object properties:

    The following three are determined by inputs:
    E = Young’s modulus
    A = Area
    I = Moment of Inertia

    The remainder are properties of the class:
    EA – (flt) Standard E * A. Standard axial stiffness of elements, default=15,000 if none provided when generating an element. 
    EI – (flt) Standard E * I. Standard bending stiffness of elements, default=5,000 if none provided when generating an element. 
    figsize – (tpl) Matplotlibs standard figure size
    element_map – (dict) Keys are the element ids, values are the element objects
    node_map – (dict) Keys are the node ids, values are the node objects.
    node_element_map – (dict) maps node ids to element objects.
    loads_point – (dict) Maps node ids to point loads.
    loads_q – (dict) Maps element ids to q-loads.
    loads_moment – (dict) Maps node ids to moment loads.
    loads_dead_load – (set) Element ids that have a dead load applied.
    '''

    # First define Object properties above
    # Most of this should be pulled from Inkslinger.
    # Values are listed for testing.

    '''
    E (Young's Modulus)
    Doug Fir-Larch #2: 1600000, Doug Fir-Larch #1: 1700000, Doug Fir-Larch SS: 1900000
    Southern Pine #2: 1400000, Southern Pine #1: 1600000, Southern Pine SS: 1800000
    Hem-Fir #2: 1300000, Spruce-Pine-Fir #1/#2: 1400000, Spruce-Pine-Fir SS: 1500000
    '''
    E = float(list_EAI[0])
    E=E*6894.7572931783 # 1 psi = 6894.7572931783 N/m^2


    '''
    A (Cross-Sectional Area)
    2x4 Truss/Rafter:  w=3.5, h=1.5, a=5.25, True 2x4 Truss/Rafter: w=4, h=2, a=8
    2x6 Truss/Rafter: w=5.5, h=	1.5, a=8.25, True 2x6 Truss/Rafter: w=6, h=2, a=12
    2x8 Rafter: w=7.25, h=1.5, a=10.875, 2x10 Rafter: w=9.25, h=1.5, a=13.875
    2x12 Rafter: w=11.25, h=1.5, a=16.875, 4x4 Rafter: w=3.5, h=3.5, a=12.25
    4x6 Rafter: w=5.5, h=3.5, a=19.25, 4x8 Rafter: w=7.25, h=3.5, a=25.375
    4x10 Rafter: w=9.25, h=3.5, a=32.375, 4x12 Rafter: w=11.25, h=3.5, a=39.375
    '''
    A = float(list_EAI[1])
    A=A*0.00064516 # 1 square inch = 0.00064516 m^2


    '''
    I (Moment of Inertia)
    2x4 Truss/Rafter: 5.36, True 2x4 Truss/Rafter: 10.67
    2x6 Truss/Rafter: 20.80, True 2x6 Truss/Rafter: 36.00
    2x8 Rafter: 47.63, 2x10 Rafter: 98.93, 2x12 Rafter: 177.98
    4x4 Rafter: 12.51, 4x6 Rafter: 48.53, 4x8 Rafter: 111.15
    4x10 Rafter: 230.84, 4x12 Rafter: 415.28
    '''
    I = float(list_EAI[2])
    I=I*.000000416231426 # inch^4 = 4.16231426 × 10-7 meters^4


    # Initialize System Elements Object
    ss = SystemElements(EA=E*A,EI=E*I)

    # Use member coordinates array to build structure
    # members are defined by start and stop points
    for i in range(0,len(member_coordinates)-1):    
        arrayValue1 = member_coordinates[i]
        arrayValue2 = member_coordinates[i+1]
        ss.add_element(location=[arrayValue1,arrayValue2])


    # Add Supports to proper positions on beam
    for i in support_coordinates:
        support_node_id = ss.find_node_id(i)
        if support_node_id == len(ss.node_map):
            ss.add_support_hinged(node_id=support_node_id)
        else:
            ss.add_support_hinged(node_id=support_node_id)


    # Identify PV start and stop points in structure
    PV_start = []
    PV_stop = []

    ndx=0
    for i in mod_coordinates:
        mod_node_id = ss.find_node_id(i)
        if (ndx % 2) == 0:
            PV_start.append(mod_node_id)
            ndx += 1
        else:
            PV_stop.append(mod_node_id)
            ndx += 1

    PV_elements = []
    nonPV_elements = []
    all_elements = []

    # Identify PV and non-PV elements, create array
    PVi=0
    for i in range(0,len(ss.node_map)):
        if i!=0:
            if i >= PV_start[PVi] and i < PV_stop[PVi]:           
                PV_elements.append(i)
            else:        
                nonPV_elements.append(i)
            if i == PV_stop[PVi]:
                if PVi == len(PV_start)-1:
                    pass
                else:
                    PVi+=1


    all_elements = PV_elements + nonPV_elements

    # Create load cases for PV vs nonPV
    # q_loads are all in N/m, and take in floats
    # Wind is set to default of 16psf for testing.

    # Define loads with psf values (anaStruct uses N/m as default, conversion happens at the end of load definition)

    '''
    Definitions for nonPV Load
    DL: 10 for shingle, 14 for tile; snow load is ground snow(Pg)*Cs factor*0.7
    LL: pitch<=18 degrees is 20psf, >=45 degrees is 12psf, in between we interpolate
    '''
    # Dead Load
    if roof_type == "shingle":
        nonPV_DL = float(10)
    elif roof_type == "tile":
        nonPV_DL = float(14)
    else: #metal roof
        nonPV_DL = float(8)

    # Snow Load
    PV_snow = snow[0]
    nonPV_snow = snow[1]

    # Dead Load
    if racking == "FM":
        PV_DL = float(nonPV_DL+3)
    elif racking =="TK":
        PV_DL = float(nonPV_DL+4)
    else:
        PV_DL = float(nonPV_DL+3)

    # Live Load
    PV_LL = 0
    # nonPV_LL = nonPV_LL


    '''
    print(f"PV Snow in psf is {PV_snow} and nonPV Snow in psf is {nonPV_snow}")
    print(f"PV Dead load in psf is {PV_DL} and nonPV Dead Load in psf is {nonPV_DL}")
    print(f"PV Live Load in psf is 0 and nonPV Live Load in psf is {nonPV_LL}")
    print(f"PV Snow Load in psf is {PV_snow} and nonPV Snow Load in psf is {nonPV_snow}")
    print(f"Wind Load in psf is {wind_load}")
    '''


    # IEBC Check with psf Values
    # Determine governing Load Combination
    # D, D + L, D + S, D + 0.75L + 0.75S
    IEBC_nonPV_DL = nonPV_DL
    IEBC_nonPV_DL_LL = nonPV_DL + nonPV_LL
    IEBC_nonPV_DL_S = nonPV_DL + nonPV_snow
    IEBC_nonPV_DL_075LL_075S = nonPV_DL + (0.75*nonPV_LL) + (0.75*nonPV_snow)

    IEBC_PV_DL = PV_DL
    IEBC_PV_DL_S = PV_DL + PV_snow

    IEBC_string = f"{IEBC_nonPV_DL}\n{IEBC_nonPV_DL_LL}\n{IEBC_nonPV_DL_S}\n{IEBC_nonPV_DL_075LL_075S}\n{IEBC_PV_DL}\n{IEBC_PV_DL_S}"
    # print(f"IEBC Loads: {IEBC_string}")


    # Convert all loads (currently in psf) to Nm
    # # Wind load will act on a localized y vector (default q_load direction) uniform across the member
    # 1 psf = 47.880258888889 N/m^2
    nonPV_DL = nonPV_DL*47.880258888889
    nonPV_LL = nonPV_LL*47.880258888889
    PV_DL = PV_DL*47.880258888889

    nonPV_snow = nonPV_snow*47.880258888889
    PV_snow = PV_snow*47.880258888889

    wind_load = wind_load*47.880258888889
    wind_up = wind_up*47.880258888889

    # print(f"nonPV DL is {nonPV_DL} in N/m^2\nnonPV LL is {nonPV_LL} in N/m^2\nnonPV snow load is {nonPV_snow} in N/m^2\nPV DL is {PV_DL} in N/m^2\nPV snow load is {PV_snow} in N/m^2\nWind Load is {wind_load} in N/m^2\n")


    # Then, convert all loads to line loads (member_spacing in m)
    nonPV_DL = nonPV_DL*member_spacing # local y direction
    nonPV_LL = nonPV_LL*member_spacing # local y direction
    PV_DL = PV_DL*member_spacing # local y direction

    nonPV_snow = nonPV_snow*member_spacing # local y direction
    PV_snow = PV_snow*member_spacing # local y direction

    wind_load = wind_load*member_spacing # local y
    wind_up = wind_up*member_spacing # local y

    # print(f"N-m\nnonPV DL is {nonPV_DL} in N/m\nnonPV LL is {nonPV_LL} in N/m\nnonPV snow load is {nonPV_snow} in N/m\nPV DL is {PV_DL} in N/m\nPV snow load is {PV_snow} in N/m\nWind Load is {wind_load} in N/m\n")


    # Convert global Y loads to global Y Direction using cosine function
    nonPV_DL = nonPV_DL*np.cos(pitch) # Global Y direction
    nonPV_LL = nonPV_LL*np.cos(pitch)*np.cos(pitch) # Request to add cosine to Python for LL + S in order to match Sizer (3/2/20)
    PV_DL = PV_DL*np.cos(pitch) # Global Y direction

    nonPV_snow = nonPV_snow*np.cos(pitch)*np.cos(pitch) # Request to add cosine to Python for LL + S in order to match Sizer (3/2/20)
    PV_snow = PV_snow*np.cos(pitch)*np.cos(pitch) # Request to add cosine to Python for LL + S in order to match Sizer (3/2/20)

    #Wind Load stays in localized Y direction.

    # print(f"nonPV DL after cos is {nonPV_DL} in N/m\nnonPV LL after cos is {nonPV_LL} in N/m\nnonPV snow load after cos is {nonPV_snow} in N/m\nPV DL after cos is {PV_DL} in N/m\nPV snow load after cos is {PV_snow} in N/m\nWind Load is {wind_load} in N/m\n")

    '''
    Load combinations to test in accordance with: ASCE 7-16, Section 2.4.1

    DL
    DL + LL
    DL + LL or snow_load
    DL + LL + 0.75*snow_load
    DL + 0.6*wind_load
    DL + 0.75*LL + 0.75*0.6*wind_load + 0.75*snow_load
    0.6*DL + 0.6*wind_load
    '''

    # Define all load cases for all combinations

    # DL factors: 1 and 0.6
    nonPV_DL_1 = nonPV_DL
    nonPV_DL_06 = nonPV_DL*0.6
    PV_DL_1 = PV_DL
    PV_DL_06 = PV_DL*0.6

    # LL factors: 1 and 0.75
    nonPV_LL_1 = nonPV_LL
    nonPV_LL_075 = nonPV_LL*0.75

    # Snow load factors: 1 and 0.75
    nonPV_snow_1 = nonPV_snow
    nonPV_snow_075 = nonPV_snow*0.75
    PV_snow_1 = PV_snow
    PV_snow_075 = PV_snow*0.75

    # Wind load factors: 1, 0.6, 0.45
    wind_1 = wind_load
    wind_06 = wind_load*0.6
    wind_045 = wind_load*0.45


    '''
    Create load cases
    '''

    # DL
    lc_DL_nonPV = LoadCase("DL_nonPV")
    lc_DL_nonPV.q_load(q=-(nonPV_DL),element_id=nonPV_elements,direction="element")
    lc_DL_PV = LoadCase("DL_PV")
    lc_DL_PV.q_load(q=-(PV_DL),element_id=PV_elements,direction="element")

    # DL + LL
    lc_DL_LL_nonPV = LoadCase("DL_LL_nonPV")
    lc_DL_LL_nonPV.q_load(q=-(nonPV_DL+nonPV_LL),element_id=nonPV_elements,direction="element")
    lc_DL_LL_PV = LoadCase("DL_LL_PV")
    lc_DL_LL_PV.q_load(q=-(PV_DL),element_id=PV_elements,direction="element")

    # DL + wind_045 + LL_075
    lc_DL_LL_075_wind_045_live_075_nonPV = LoadCase("DL_LL_075_wind_045_live_075_nonPV")
    lc_DL_LL_075_wind_045_live_075_nonPV.q_load(q=-(nonPV_DL+wind_045+nonPV_LL_075),element_id=nonPV_elements,direction="element")
    lc_DL_LL_075_wind_045_live_075_PV = LoadCase("DL_LL_075_wind_045_live_075_PV")
    lc_DL_LL_075_wind_045_live_075_PV.q_load(q=-(PV_DL+wind_045),element_id=PV_elements,direction="element")

    # DL + snow
    lc_DL_snow_nonPV = LoadCase("DL_snow_nonPV")
    lc_DL_snow_nonPV.q_load(q=-(nonPV_DL+nonPV_snow),element_id=nonPV_elements,direction="element")
    lc_DL_snow_PV = LoadCase("DL_snow_PV")
    lc_DL_snow_PV.q_load(q=-(PV_DL+PV_snow),element_id=PV_elements,direction="element")

    # DL + wind_045 + snow_075
    lc_DL_LL_075_wind_045_snow_075_nonPV = LoadCase("DL_LL_075_wind_045_snow_075_nonPV")
    lc_DL_LL_075_wind_045_snow_075_nonPV.q_load(q=-(nonPV_DL+wind_045+nonPV_snow_075),element_id=nonPV_elements,direction="element")
    lc_DL_LL_075_wind_045_snow_075_PV = LoadCase("DL_LL_075_wind_045_snow_075_PV")
    lc_DL_LL_075_wind_045_snow_075_PV.q_load(q=-(PV_DL+wind_045+PV_snow_075),element_id=PV_elements,direction="element")

    # DL_06 + wind_06_up
    lc_DL_06_wind_06_nonPV = LoadCase("DL_06_wind_06_nonPV")
    lc_DL_06_wind_06_nonPV.q_load(q=-(nonPV_DL_06+wind_up),element_id=nonPV_elements,direction="element")
    lc_DL_06_wind_06_PV = LoadCase("DL_06_wind_06_PV")
    lc_DL_06_wind_06_PV.q_load(q=-(PV_DL_06+wind_up),element_id=PV_elements,direction="element")

    # DL + wind_06_down
    lc_DL_wind_06_nonPV = LoadCase("DL_wind_06_nonPV")
    lc_DL_wind_06_nonPV.q_load(q=-(nonPV_DL+wind_06),element_id=nonPV_elements,direction="element")
    lc_DL_wind_06_PV = LoadCase("DL_wind_06_PV")
    lc_DL_wind_06_PV.q_load(q=-(PV_DL+wind_06),element_id=PV_elements,direction="element")

    final_result_string = ""

    # Apply load cases to elements (load cases overwrite if applied to the same element)

    for i in range(1,8):
        if i==1:
            # DL
            ss.apply_load_case(lc_DL_nonPV)
            ss.apply_load_case(lc_DL_PV)
            load_combination = "D"

        if i==2:
            # DL + LL
            ss.apply_load_case(lc_DL_LL_nonPV)
            ss.apply_load_case(lc_DL_LL_PV)
            load_combination = "D + Lr"

        if i==3:
            # DL + LL_075 + wind_045
            ss.apply_load_case(lc_DL_LL_075_wind_045_live_075_nonPV)
            ss.apply_load_case(lc_DL_LL_075_wind_045_live_075_PV)
            load_combination = "D + 0.75(Lr + 0.6W)"

        if i==4:
            # DL + S
            ss.apply_load_case(lc_DL_snow_nonPV)
            ss.apply_load_case(lc_DL_snow_PV)
            load_combination = "D + S"

        if i==5:
            # DL + wind_045 + snow_075
            ss.apply_load_case(lc_DL_LL_075_wind_045_snow_075_nonPV)
            ss.apply_load_case(lc_DL_LL_075_wind_045_snow_075_PV)
            load_combination = "D + 0.75(S + 0.6W)"

        if i==6:
            # DL_06 + wind_06_up
            ss.apply_load_case(lc_DL_06_wind_06_nonPV)
            ss.apply_load_case(lc_DL_06_wind_06_PV)
            load_combination = "0.6D + 0.6W (Up)"

        if i==7:
            # DL + wind_06_down
            ss.apply_load_case(lc_DL_wind_06_nonPV)
            ss.apply_load_case(lc_DL_wind_06_PV)
            load_combination = "D + 0.6W (Down)"

        # Solve and display results
        ss.solve()

        #Obtain shear array via anaStruct, since the shear values do not appear in the element_results used for the other values.
        shear_results = ss.get_element_result_range("shear")

        #Shear results only provide V(+) positive shear
        positive_shear_array = []
        for data in shear_results:
            positive_shear_array.append(data)

        #Add a 0 to the end to match node array length (shear at end is 0)
        positive_shear_array.append(0)

        #Use reaction forces to obtain V(-) negative shear values at nodes
        rxn_forces = ss.get_node_results_system(node_id=0)
        rxn_array = []
        for data in rxn_forces:
            rxn_array.append(data[2]/np.cos(pitch))

        negative_shear_array = []
        for i in range(0,len(positive_shear_array)):
            negative_shear_array.append(positive_shear_array[i]-rxn_array[i])

        #Consider all shears, and find highest magnitude
        total_shear = positive_shear_array + negative_shear_array
        max_shear = max(map(abs,total_shear))

        max_moment_positive = 0
        max_moment_negative = 0
        max_axial = 0
        max_displacement = 0

        element_result_string = str(ss.get_element_results(element_id=0, verbose=True))

        for results in ss.get_element_results(element_id=0, verbose=True):
            tmp_Mmax = results["Mmax"]
            if tmp_Mmax > max_moment_positive:
                max_moment_positive = tmp_Mmax
            tmp_Mmin = results["Mmin"]
            if tmp_Mmin < max_moment_negative:
                max_moment_negative = tmp_Mmin

            tmp_N = abs(results["N"])
            if tmp_N > max_axial:
                max_axial = tmp_N

            tmp_w = (max(abs(results["w"]))/np.cos(pitch))
            if tmp_w>max_displacement:
                max_displacement = tmp_w


        # Moment Value signs are reversed in anaStruct, so this looks weird but is designed to get our own signs
        max_moment_positive = -np.ceil(max_moment_positive*0.737562149) # Conversion from Nm to lb-ft
        max_moment_negative = -np.ceil(max_moment_negative*0.737562149) # Conversion from Nm to lb-ft
        max_shear = np.ceil(max_shear*0.22480894244319) # Conversion from N to lb
        max_axial = np.ceil(max_axial*0.22480894244319) # Conversion from N to lb

        displacement_array = ss.get_node_displacements()
        # print(displacement_array)
        
        for i in displacement_array:
            tmp_w = (abs(i[2])/np.cos(pitch))
            if tmp_w>max_displacement:
                max_displacement = tmp_w
        
        
        # Convert to inches after comparison is done
        max_displacement = max_displacement*39.3700787 # Conversion from m to in.

        # Moment Value signs are reversed in anaStruct, so this looks weird but is designed to get our own signs
        max_result_string = f"{load_combination}:\n" + f"{max_moment_positive}" + f"\n{max_moment_negative}" + f"\n{max_shear}" + f"\n{max_axial}" + f"\n{max_displacement}" + f"\n\n"
        final_result_string = final_result_string + max_result_string
        final_result_string = final_result_string 
        
    final_result_string = final_result_string + "IEBC Load Check:\n" + IEBC_string

    return final_result_string