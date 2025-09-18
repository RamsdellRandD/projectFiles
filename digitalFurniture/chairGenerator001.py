import bpy; import bmesh
import numpy as np; from mathutils import Matrix, Vector
import time

#clear out "generated chairs" collection
for obj in bpy.data.scenes[0].collection.objects:
    bpy.data.objects.remove(obj)

#purge unused meshes
for mesh in bpy.data.meshes:
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)

        
#set chair parameters
h = .6 #seat height, m
w = .6 #seat width, m
d = .45 #seat depth, m
b = .4 #back height, m
a = 15 #back angle, degrees

#secondary parameters
t = 0.0125 #seat and back thickness, m
lft = 0.075 #thickness at top of front leg, m
lbt = 0.045 #x-thickness of back leg
sw = .08 #vertical width of the supports under the seat, m

a = (a/360) * 2*np.pi #convert a to radians


#functions for individual components of the chair
def autoSeat001(h, w, d, t):
    '''creates a rectangular prism seat for the chair
    based on given parameters'''
    
    #create seat object and mesh
    seatMe = bpy.data.meshes.new("genSeat.001")
    seatOb = bpy.data.objects.new("genSeat.001", seatMe)
    bpy.data.scenes[0].collection.objects.link(seatOb)
    
    #create seat geometry
    seatBM = bmesh.new()
    bmesh.ops.create_cube(seatBM, size = 1, matrix = Matrix((
    (w, 0, 0, 0),
    (0, d, 0, 0), 
    (0, 0, t, h-t/2), 
    (0, 0, 0, 1))))
    
    #push seat geometry to seat object
    seatBM.to_mesh(seatMe)
    seatMe.update()
    seatBM.free()
    
    
def autoFrontLegs001(h, w, d, t, lft):
    '''creates the front legs of the chair based on given parameters'''
    
    #define some geometric parameters
    legFLength = h - t
    legFCenX = w/2 - lft/2 #x-coord of center of leg
    legFCenZ = legFLength / 2 #z-coord of center of leg
    legFCenY = d/2 - lft/2 #y-coord of center of leg
    
    numLegs = np.floor(w) + 1
    legSpacing = (w - lft) / numLegs
        
    #create object and mesh
    legFMe = bpy.data.meshes.new("genLegF.001")
    legFOb = bpy.data.objects.new("genLegF.001", legFMe)
    bpy.data.scenes[0].collection.objects.link(legFOb)
    
    #create geometry
    legFBM = bmesh.new()
    bmesh.ops.create_cube(legFBM, size = 1, matrix = Matrix((
    (lft, 0, 0, legFCenX),
    (0, lft, 0, legFCenY), 
    (0, 0, legFLength, legFCenZ), 
    (0, 0, 0, 1))))
    
    #modify geometry to add taper
    legFBM.verts.ensure_lookup_table()
    
    for i in (0, 2):
        v = legFBM.verts[i]
        v.co.x = v.co.x + 0.125 * lft #bring inner side out
        
    for i in (0, 4):
        v = legFBM.verts[i]
        v.co.y = v.co.y + 0.125 * lft #bring back side forward
        
    for i in (4, 6):
        v = legFBM.verts[i]
        v.co.x = v.co.x - 0.125 * lft #bring outer side in
        
    for i in (2, 6):
        v = legFBM.verts[i]
        v.co.y = v.co.y - 0.125 * lft #bring front side back
    
    legFBM.to_mesh(legFMe)
    
    #duplicate the appropriate number of legs
    for i in range(int(numLegs)):
        workBM = bmesh.new() #create a "working bmesh" to hold the new leg
        workBM.from_mesh(legFMe) #pull the new leg in 
        workBM.verts.ensure_lookup_table()
        
        for j in range(int(len(workBM.verts))): 
            v = workBM.verts[j]
            v.co.x -= legSpacing #move the new leg over
        
        workBM.to_mesh(legFMe) #push the new leg to the mesh for holding
        workBM.free() #free up working bmesh
        
        legFBM.from_mesh(legFMe) #add the new leg to the lineup in master bmesh
    
    #push final leg situation to the mesh
    legFBM.to_mesh(legFMe)
    legFMe.update()
    legFBM.free()
    
 
    
def autoBackLegs001(h, w, d, b, a, t, lft, lbt, sw):
    '''creates the back legs of the chair based on given parameters
    (the back legs also include the support for the backrest)'''
    
    #define some geometric parameters
    legBLength = h + b
    legBCenX = w/2 - lbt/2 #x-coord of center of leg
    legBCenZ = legBLength / 2 #z-coord of center of leg
    legBCenY = (-1 * d)/2 - lft/2 #y-coord of center of leg
    
    cut1Z = h - t - sw #position of lower loop cut
    cut2Z = (b / 3) + h #position of upper loop cut
    
    backOffset = (h + b - cut2Z) * np.tan(a) #horizontal offset calculated from back angle
    
    numLegs = np.floor(w) + 1 #number of EXTRA legs
    legSpacing = (w - lbt) / numLegs
    
    #create object and mesh
    legBMe = bpy.data.meshes.new("genLegB.001")
    legBOb = bpy.data.objects.new("genLegB.001", legBMe)
    bpy.data.scenes[0].collection.objects.link(legBOb)
    
    #create geometry
    legBBM = bmesh.new()
    bmesh.ops.create_cube(legBBM, size = 1, matrix = Matrix((
    (lbt, 0, 0, legBCenX),
    (0, lft, 0, legBCenY), 
    (0, 0, legBLength, legBCenZ), 
    (0, 0, 0, 1))))
    
    #modify geometry
    legBBM.edges.ensure_lookup_table()
    
    #add loop cuts to the leg
    cutEdges = (legBBM.edges[1], legBBM.edges[3], legBBM.edges[6], legBBM.edges[9]) 
    bmesh.ops.subdivide_edges(legBBM, edges = cutEdges, cuts = 2, use_grid_fill = True)
    
    #position loop cuts correctly
    legBBM.verts.ensure_lookup_table()
    
    for i in (8, 11, 13, 15): #lower loop cut
        v = legBBM.verts[i]
        v.co.z = cut1Z
        
    for i in (9, 10, 12, 14): #upper loop cut
        v = legBBM.verts[i]
        v.co.z = cut2Z
    
    #taper bottom of leg
    for i in (2, 6):
        v = legBBM.verts[i]
        v.co.y -= lft / 3
        
    #angle back support and taper top
    for i in (1, 3, 5, 7):
        v = legBBM.verts[i]
        v.co.y -= backOffset
        
    for i in (1, 5):
        v = legBBM.verts[i]
        v.co.y += lft / 3
    
    legBBM.to_mesh(legBMe)
     
    #duplicate the appropriate number of legs
    for i in range(int(numLegs)):
        workBM = bmesh.new()
        workBM.from_mesh(legBMe)
        workBM.verts.ensure_lookup_table()
        
        for j in range(int(len(workBM.verts))):
            v = workBM.verts[j]
            v.co.x -= legSpacing
        
        workBM.to_mesh(legBMe)
        workBM.free()
        
        legBBM.from_mesh(legBMe)
    
    #push geometry to object
    legBBM.to_mesh(legBMe)
    legBMe.update()
    legBBM.free()
    
    
def autoBack001(h, w, d, b, a, t, lft, lbt, sw):
    '''creates the backrest of the chair based on given parameters'''
    
    #define some geometric parameters
    numBacks = np.floor(w) #number of EXTRA backs
    
    cut2Z = (b / 3) + h #position of upper loop cut
    backHeight = h + b - cut2Z #vertical width of back panel
    backWidth = (w - (lbt * (numBacks + 2))) / (numBacks + 1)
    backOffset = backHeight * np.tan(a) #horizontal offset calculated from back angle
    backCenY = -1 * (d / 2 + t / 2)
    backCenZ = (h + b) - (backHeight / 2)
    backCenX = (w / 2) - lbt - (backWidth / 2)
    
    backSpacing = (w - lbt) / (numBacks + 1)
    
    #create object and mesh
    backMe = bpy.data.meshes.new("genBack.001")
    backOb = bpy.data.objects.new("genBack.001", backMe)
    bpy.data.scenes[0].collection.objects.link(backOb)
    
    #create geometry
    backBM = bmesh.new()
    bmesh.ops.create_cube(backBM, size = 1, matrix = Matrix((
    (backWidth, 0, 0, backCenX),
    (0, t, 0, backCenY), 
    (0, 0, backHeight, backCenZ), 
    (0, 0, 0, 1))))
    
    #modify geometry to add angle
    backBM.verts.ensure_lookup_table()
    
    for i in (1, 3, 5, 7):
        v = backBM.verts[i]
        v.co.y -= backOffset #bring inner side in
    
    backBM.to_mesh(backMe)
    
    #duplicate the appropriate number of backs
    for i in range(int(numBacks)):
        workBM = bmesh.new()
        workBM.from_mesh(backMe)
        workBM.verts.ensure_lookup_table()
        
        for j in range(int(len(workBM.verts))):
            v = workBM.verts[j]
            v.co.x -= backSpacing
        
        workBM.to_mesh(backMe)
        workBM.free()
        
        backBM.from_mesh(backMe)
    
    #push geometry to object
    backBM.to_mesh(backMe)
    backMe.update()
    backBM.free()
    

def autoFrontStruts001(h, w, d, t, lft, lbt, sw):
    '''creates the front struts of the chair based on given parameters'''
    
    #define some geometric parameters
    numStruts = np.floor(w) #number of EXTRA backs
    
    strutWidth = (w - (lft * (numStruts + 2))) / (numStruts + 1) #horizontal width of the struts
    strutCenY = d / 2 - t / 2
    strutCenZ = h - t - sw / 2
    strutCenX = (w / 2) - lft - (strutWidth / 2)
    
    strutSpacing = (w - lft) / (numStruts + 1)
    
    #create object and mesh
    strutFMe = bpy.data.meshes.new("genStrutF.001")
    strutFOb = bpy.data.objects.new("genStrutF.001", strutFMe)
    bpy.data.scenes[0].collection.objects.link(strutFOb)
    
    #create geometry
    strutFBM = bmesh.new()
    bmesh.ops.create_cube(strutFBM, size = 1, matrix = Matrix((
    (strutWidth, 0, 0, strutCenX),
    (0, t, 0, strutCenY), 
    (0, 0, sw, strutCenZ), 
    (0, 0, 0, 1))))
    
    strutFBM.to_mesh(strutFMe)
    
    #duplicate the appropriate number of struts
    for i in range(int(numStruts)):
        workBM = bmesh.new()
        workBM.from_mesh(strutFMe)
        workBM.verts.ensure_lookup_table()
        
        for j in range(int(len(workBM.verts))):
            v = workBM.verts[j]
            v.co.x -= strutSpacing
        
        workBM.to_mesh(strutFMe)
        workBM.free()
        
        strutFBM.from_mesh(strutFMe)
    
    #push geometry to object
    strutFBM.to_mesh(strutFMe)
    strutFMe.update()
    strutFBM.free()
    
def autoBackStruts001(h, w, d, t, lft, lbt, sw):
    '''creates the back struts of the chair based on given parameters'''
    
    #define some geometric parameters
    numStruts = np.floor(w) #number of EXTRA backs
    
    strutWidth = (w - (lbt * (numStruts + 2))) / (numStruts + 1) #horizontal width of the struts
    strutCenY = -1 * (d / 2 + t / 2)
    strutCenZ = h - sw / 2
    strutCenX = (w / 2) - lbt - (strutWidth / 2)
    
    strutSpacing = (w - lbt) / (numStruts + 1)
    
    #create object and mesh
    strutBMe = bpy.data.meshes.new("genStrutB.001")
    strutBOb = bpy.data.objects.new("genStrutB.001", strutBMe)
    bpy.data.scenes[0].collection.objects.link(strutBOb)
    
    #create geometry
    strutBBM = bmesh.new()
    bmesh.ops.create_cube(strutBBM, size = 1, matrix = Matrix((
    (strutWidth, 0, 0, strutCenX),
    (0, t, 0, strutCenY), 
    (0, 0, sw, strutCenZ), 
    (0, 0, 0, 1))))
    
    strutBBM.to_mesh(strutBMe)
    
    #duplicate the appropriate number of struts
    for i in range(int(numStruts)):
        workBM = bmesh.new()
        workBM.from_mesh(strutBMe)
        workBM.verts.ensure_lookup_table()
        
        for j in range(int(len(workBM.verts))):
            v = workBM.verts[j]
            v.co.x -= strutSpacing
        
        workBM.to_mesh(strutBMe)
        workBM.free()
        
        strutBBM.from_mesh(strutBMe)
    
    #push geometry to object
    strutBBM.to_mesh(strutBMe)
    strutBMe.update()
    strutBBM.free()
    
    
def autoSideStruts001(h, w, d, t, lft, lbt, sw):
    '''creates the side struts of the chair based on given parameters'''
    
    #define some geometric parameters
    numStruts = np.floor(w) + 1 #number of EXTRA backs
    
    strutWidth = d - lft #front-to-back width of the struts
    strutCenY = -1 * (lft / 2)
    strutCenZ = h - t - sw / 2
    strutCenX = w / 2 - t / 2
    
    strutSpacing = (w - t) / numStruts
    
    #create object and mesh
    strutSMe = bpy.data.meshes.new("genStrutS.001")
    strutSOb = bpy.data.objects.new("genStrutS.001", strutSMe)
    bpy.data.scenes[0].collection.objects.link(strutSOb)
    
    #create geometry
    strutSBM = bmesh.new()
    bmesh.ops.create_cube(strutSBM, size = 1, matrix = Matrix((
    (t, 0, 0, strutCenX),
    (0, strutWidth, 0, strutCenY), 
    (0, 0, sw, strutCenZ), 
    (0, 0, 0, 1))))
    
    strutSBM.to_mesh(strutSMe)
    
    #duplicate the appropriate number of struts
    for i in range(int(numStruts)):
        workBM = bmesh.new()
        workBM.from_mesh(strutSMe)
        workBM.verts.ensure_lookup_table()
        
        for j in range(int(len(workBM.verts))):
            v = workBM.verts[j]
            v.co.x -= strutSpacing
        
        workBM.to_mesh(strutSMe)
        workBM.free()
        
        strutSBM.from_mesh(strutSMe)
    
    #push geometry to object
    strutSBM.to_mesh(strutSMe)
    strutSMe.update()
    strutSBM.free()
    
    
autoSeat001(h, w, d, t)
autoFrontLegs001(h, w, d, t, lft)
autoBackLegs001(h, w, d, b, a, t, lft, lbt, sw)
autoBack001(h, w, d, b, a, t, lft, lbt, sw)
autoFrontStruts001(h, w, d, t, lft, lbt, sw)
autoBackStruts001(h, w, d, t, lft, lbt, sw)
autoSideStruts001(h, w, d, t, lft, lbt, sw)








        
