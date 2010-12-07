#!BPY
"""
Name: 'XML3D M4 (.xhtml) ...'
Blender: 248
Group: 'Export'
Tooltip: 'Export scene to XML3D'
"""

__author__ = "Kristian Sons"
__url__ = ("blender", "blenderartists.org", "XML3D homepage, http://www.xml3d.org", "XML3D exporter, http://github.com/xml3d/XML3D-Exporters")
__version__ = "DEV_VERSION"
__bpydoc__ = """
Description:

Exports Blender scene into XML3D format.

Usage: run the script from the menu or inside Blender.  

Notes: the script does not export animations yet.
"""

# --------------------------------------------------------------------------
# XML3D exporter 
# --------------------------------------------------------------------------
# ***** BEGIN GPL LICENSE BLOCK *****
#
# Copyright (C) 2010: DFKI GmbH, kristian.sons@dfki.de
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****
# --------------------------------------------------------------------------

from xml3d import XML3DDocument
import sys

import Blender, bpy, BPyMesh #@UnresolvedImport
from Blender import Mesh, Window, Mathutils, Material #@UnresolvedImport

DEG2RAD = 0.017453292519943295

class vertex:
    index = None
    normal = None
    texcoord = None
    color = None
    
    def veckey3d(self, v):
        if v == None:
            return None
        return Mathutils.Vector(round(v.x, 8), round(v.y, 8), round(v.z, 8))

    def veckey2d(self, v):
        if v == None:
            return None
        return Mathutils.Vector(round(v.x, 8), round(v.y, 8))

    def __init__(self, index, normal = None, texcoord = None, color = None):
        self.index = index
        self.normal = self.veckey3d(normal)
        self.texcoord = self.veckey2d(texcoord)
    
    def __str__( self ) :
        return "i: " + str( self.index ) + ", n: " + str( self.normal ) + ", t: " + str( self.texcoord )
 
    def __cmp__(self, other):
        "Currently not used as __eq__ has higher priority"
        #print "Compare"
        if self.index < other.index:
            return -1;
        if self.index > other.index:
            return 1;
        
        if self.normal != other.normal:
            if self.normal == None:
                return -1;
            if other.normal == None:
                return 1;
            return cmp(self.normal, other.normal)

        if self.texcoord != other.texcoord:
            if self.texcoord == None:
                return -1;
            if other.texcoord == None:
                return 1;
            return cmp(self.texcoord, other.texcoord)

        return 0;
 
    def __hash__( self ) :
        return self.index

                   
    def __eq__(self, other):
        return self.index == other.index and self.normal == other.normal and self.texcoord == other.texcoord
        

def appendUnique(mlist, value):
    if value in mlist:
        return mlist[value], False
    # Not in dict, thus add it
    index = len(mlist)
    mlist[value] = index
    return index, True    
    
class xml3d_exporter:
    
    annotatePhysics = False
    noMaterialAppeared = False
    doc = None
    
    def __init__(self, filename, withGUI):
        self.filename = filename
        self.withGUI = withGUI
        #doc = xml.dom.minidom.Document()
       
        
    def getContainerMesh(self, createNew=True):
        temp_mesh_name = '~tmp-mesh'
        containerMesh = meshName = tempMesh = None
        for meshName in Blender.NMesh.GetNames():
            if meshName.startswith(temp_mesh_name):
                tempMesh = Mesh.Get(meshName)
                if not tempMesh.users:
                    containerMesh = tempMesh
        if not containerMesh and createNew:
            containerMesh = Mesh.New(temp_mesh_name)
        del meshName
        del tempMesh
        return containerMesh
    
    def writeMeshObject(self, obj, parent):
        #print 'Writing: ' , obj.name
        
        aMesh = obj.getData()

        group = self.doc.createGroupElement()
        parent.appendChild(group)
        group.setTransform("#t_" + obj.name)

        if ( self.annotatePhysics ):
            group.setAttribute("physics-material", "#phy_" + obj.name)
        
        matCount = len(aMesh.materials)
        if matCount < 2:
            self.writeDefaultShader()
            if matCount == 0:
                group.setShader("#_no_mat")
            else:
                group.setShader("#" + aMesh.materials[0].name)
            mesh = self.doc.createMeshElement(None, None, "triangles", "#" + aMesh.name + "_data")
            group.appendChild(mesh)
        else:
            for material in aMesh.materials:
                shaderName = "#" + material.name
                subgroup = self.doc.createGroupElement(shader_ = shaderName)
                group.appendChild(subgroup)
                mesh = self.doc.createMeshElement(type_ = "triangles")
                mesh.setSrc("#" + aMesh.name + "_data_" + material.name)
                subgroup.appendChild(mesh)
            
        
        

    def writeMeshData(self, parent, mesh, obj):
        
        aMesh = BPyMesh.getMeshFromObject(obj, self.getContainerMesh(), True, scn=self.scene)
        
        if len(aMesh.faces) == 0:
            return
        
        print("Writing mesh %s" % mesh.name)
        
        materials = aMesh.materials
        
        has_quads = False
        for f in aMesh.faces:
            if len(f) == 4:
                has_quads = True
                break
        
        if has_quads:
            oldmode = Mesh.Mode()
            Mesh.Mode(Mesh.SelectModes['FACE'])
            
            aMesh.sel = True
            tempob = self.scene.objects.new(aMesh)
            aMesh.quadToTriangle(0) # more=0 shortest length
            oldmode = Mesh.Mode(oldmode)
            self.scene.objects.unlink(tempob)
            
            Mesh.Mode(oldmode)
        
        data = self.doc.createDataElement(mesh.name+"_data", None, None, None, None)    
        parent.appendChild(data)
        
        # Mesh indices
        matCount = len(materials)
        if matCount == 0:
            matCount = 1
        indices = [[] for m in range(matCount)] #@UnusedVariable
        vertices = []
        vertex_dict = {}
       
        print("Faces: %i" % len(aMesh.faces))
        
        i = 0
        for face in aMesh.faces:
            mv = None
            for i, v in enumerate(face):
                if face.smooth:
                    if aMesh.faceUV:
                        mv = vertex(v.index, None, face.uv[i])
                    else:
                        mv = vertex(v.index, None, None)
                else:
                    if aMesh.faceUV:
                        mv = vertex(v.index, face.no, face.uv[i])
                    else:
                        mv = vertex(v.index, face.no)
                index, added = appendUnique(vertex_dict, mv)
                indices[face.mat].append(index)
                if added:
                    vertices.append(mv)


        # Single or no material: write all in one data block
        if not matCount > 1:
            valueElement = self.doc.createIntElement(None, "index")
            valueElement.setValue(' '.join(map(str, indices[0])))
            data.appendChild(valueElement)
       
        print("Vertices: %i" % len(vertex_dict))
        
        # Vertex positions
        value_list = []
        for v in vertices:
            value_list.append("%.6f %.6f %.6f" % tuple(aMesh.verts[v.index].co))
                
        valueElement = self.doc.createFloat3Element(None, "position")
        valueElement.setValue(' '.join(value_list))
        data.appendChild(valueElement)
        
        # Vertex normals
        value_list = []
        for v in vertices:
            if v.normal == None:
                value_list.append("%.6f %.6f %.6f" % tuple(aMesh.verts[v.index].no))
            else:
                value_list.append("%.6f %.6f %.6f" % tuple(v.normal))
     
        valueElement = self.doc.createFloat3Element(None, "normal")
        valueElement.setValue(' '.join(value_list))
        data.appendChild(valueElement)

        # Vertex texCoord
        if aMesh.faceUV:
            value_list = []
            for v in vertices:
                value_list.append("%.6f %.6f" % tuple(v.texcoord))
    
            valueElement =self. doc.createFloat2Element(None, "texcoord")
            valueElement.setValue(' '.join(value_list))
            data.appendChild(valueElement);
            
        if len(materials) > 1:
            for i, material in enumerate(materials):
                if len(indices[i]) == 0:
                    continue
                
                data = self.doc.createDataElement(mesh.name+"_data_" + material.name, None, None, None, None)    
                parent.appendChild(data)

                refdata = self.doc.createDataElement(src_="#"+mesh.name+"_data")
                data.appendChild(refdata)

                valueElement = self.doc.createIntElement(None, "index")
                valueElement.setValue(' '.join(map(str, indices[i])))
                data.appendChild(valueElement)
       
        aMesh.verts = None
        
        
    def writeMainDef(self, parent):
        defElement = self.doc.createDefsElement("mainDef")
        defElement.setIdAttribute( "id" )
        
        parent.appendChild(defElement)
        
        meshes, lights, cameras = {}, {}, {}
        
        print("Objects: %i" % len(bpy.data.objects))
        for obj in bpy.data.objects:
            
            if obj.restrictRender or obj.users == 0:
                continue
            
            objType = obj.getType( )
            dataName = obj.getData( True )
            data = obj.getData( False, True )
            
            if objType == 'Mesh':
                meshes[ dataName ] = data, obj
            elif objType == 'Lamp':
                lights[ dataName ] = data
            elif objType == 'Camera':
                cameras[ dataName ] = data
        
        
        for obj in bpy.data.objects:
            self.writeTransform(defElement, obj)
        
        for key in meshes:
            rawMesh, obj = meshes[ key ]
            self.writeMeshData(defElement, rawMesh, obj)
            if (self.annotatePhysics):
                self.writePhysicsMaterial(defElement, rawMesh);
        
        for lamp in bpy.data.lamps:
            self.writeLightShader(defElement, lamp)
            
        for material in bpy.data.materials:
            self.writePhongShader(defElement, material)
    
    def writeTransform(self, parent, obj):
        if obj.data.name.startswith('~tmp-mesh'):
            return
        quat = obj.matrix.rotationPart().toQuat()
        axis = quat.axis
        angle =  quat.angle * DEG2RAD
        
        transform = self.doc.createTransformElement("t_" + obj.name)
        transform.setTranslation("%.6f %.6f %.6f" % (obj.LocX, obj.LocY, obj.LocZ))
        transform.setScale("%.6f %.6f %.6f" % (obj.SizeX, obj.SizeY, obj.SizeZ))
        transform.setRotation("%.6f %.6f %.6f %.6f" % (axis.x, axis.y, axis.z, angle))
        parent.appendChild(transform)
        
    def writePhysicsMaterial(self, parent, mesh):
        
        mat = self.doc.createElement("physics:material")
        mat.setAttribute("id", "phy_" + mesh.name)
        parent.appendChild(mat)        
        
        # Set the actor type
        type = self.doc.createElement("string")
        type.setAttribute("name", "type")
        type.appendChild(self.doc.createTextNode("dynamic"))
        mat.appendChild(type)

        materials = mesh.materials
        if (len(materials) and materials[0] != None):
            # Set the friction
            frictionElement = self.doc.createElement("float")
            frictionElement.setAttribute("name", "friction")
            frictionElement.appendChild(self.doc.createTextNode(str(materials[0].rbFriction)))
            mat.appendChild(frictionElement)
    
            # Set the restitution
            restitutionElement = self.doc.createElement("float")
            restitutionElement.setAttribute("name", "restitution")
            restitutionElement.appendChild(self.doc.createTextNode(str(materials[0].rbRestitution)))
            mat.appendChild(restitutionElement)

        
        
    def writeLightShader(self, parent, light):
        # TODO: Spot Light, Directional Light
        # Blender LAMP type --> XML3D "urn:xml3d:lightshader:point"      
        if ( light.type == Blender.Lamp.Types.Lamp ):                  
            lightShaderElement = self.doc.createLightshaderElement("ls_" + light.name, "urn:xml3d:lightshader:point")
            parent.appendChild(lightShaderElement)
        
            mode = light.mode
            valueElement = self.doc.createBoolElement(None, "castShadow")
            if mode & Blender.Lamp.Modes.RayShadow or mode & Blender.Lamp.Modes.Shadows:
                valueElement.setValue("true")
            else:
                valueElement.setValue("false")
            
            lightShaderElement.appendChild(valueElement)
        
            attens = [1.0, 0.0, 0.0]
            if light.falloffType == Blender.Lamp.Falloffs.CONSTANT:
                attens = [1.0, 0.0, 0.0]
            elif light.falloffType == Blender.Lamp.Falloffs.INVLINEAR:
                attens = [1.0, 1.0 / light.dist, 0.0]
            elif light.falloffType == Blender.Lamp.Falloffs.INVSQUARE:
                attens = [1.0, 0.0, 1.0 / (light.dist * light.dist)]
            
            valueElement = self.doc.createFloat3Element(None, "attenuation")
            valueElement.setValue("%f %f %f" % tuple(attens))
            lightShaderElement.appendChild(valueElement)
        
            valueElement = self.doc.createFloat3Element(None, "intensity")
            valueElement.setValue("%f %f %f" % (light.r, light.g, light.b))
            lightShaderElement.appendChild(valueElement)
        
        
    def writeDefaultShader(self):
        if self.noMaterialAppeared:
            return
        self.noMaterialAppeared = True
        defElement = self.doc.getElementById("mainDef")
        shaderElement = self.doc.createShaderElement("_no_mat", "urn:xml3d:shader:phong");

        valueElement = self.doc.createFloat3Element(None, "diffuseColor")
        valueElement.setValue("0.3 0.3 0.3")
        shaderElement.appendChild(valueElement)
        
        valueElement = self.doc.createFloatElement(None, "ambientIntensity")
        valueElement.setValue("0.2")
        shaderElement.appendChild(valueElement)

        defElement.appendChild(shaderElement)
               
        
    def writePhongShader(self, parent, material):
        doc = self.doc
        shaderElement = doc.createShaderElement(material.name, "urn:xml3d:shader:phong");
        parent.appendChild(shaderElement)
        
        world = Blender.World.GetCurrent()
        
        valueElement = doc.createFloatElement(None, "ambientIntensity")
        if world:
            ambR, ambG, ambB = world.amb;
            valueElement.setValue(str(material.amb * ((ambR + ambG + ambB) / 3.0)))
        else:
            valueElement.setValue(str(material.amb))
            
        shaderElement.appendChild(valueElement)
        
        hasTexture = False
        for mtex in material.textures:
            if mtex == None:
                continue
            if mtex.texco == Blender.Texture.TexCo.UV and mtex.mapto == Blender.Texture.MapTo.COL:
                if mtex.tex.type == Blender.Texture.Types.IMAGE:
                    texture = doc.createTextureElement(None, "diffuseTexture")
                    img = doc.createImgElement(None, Blender.sys.basename(mtex.tex.image.filename))
                    texture.appendChild(img)
                    shaderElement.appendChild(texture)
                    hasTexture = True
                    
                    valueElement = doc.createFloat3Element(None, "diffuseColor")
                    #fac = 1.0 - mtex.colfac
                    #valueElement.setValue("%f %f %f" % (material.rgbCol[0] * fac, material.rgbCol[1] * fac, material.rgbCol[2] * fac))
                    valueElement.setValue("1 1 1")
                    shaderElement.appendChild(valueElement)
                    break;
            
        if not hasTexture:
            valueElement = doc.createFloat3Element(None, "diffuseColor")
            valueElement.setValue("%f %f %f" % tuple(material.rgbCol))
            shaderElement.appendChild(valueElement)

        
        emit = material.getEmit()
        if emit > 0.0001:
            valueElement = doc.createFloat3Element(None, "emissiveColor")
            valueElement.setValue("%f %f %f" % (material.rgbCol[0] * emit, material.rgbCol[1] * emit, material.rgbCol[2] * emit))
            shaderElement.appendChild(valueElement)
        
        valueElement = doc.createFloat3Element(None, "specularColor")
        valueElement.setValue("%f %f %f" % 
                          ((material.specCol[0] * material.spec),
                           (material.specCol[1] * material.spec),
                           (material.specCol[2] * material.spec)))
        shaderElement.appendChild(valueElement)
        
        valueElement = doc.createFloatElement(None, "shininess")
        valueElement.setValue(str(material.hard/511.0))
        shaderElement.appendChild(valueElement)
        
        transparent = 1.0 - material.alpha;
        if (transparent > 0.0001):
            valueElement = doc.createFloatElement(None, "transparency")
            valueElement.setValue(str(transparent))
            shaderElement.appendChild(valueElement)
        
        if material.mode & Material.Modes.RAYMIRROR != 0:
            valueElement = doc.createFloat3Element(None, "reflective")
            valueElement.setValue("%f %f %f" % (material.rayMirr, material.rayMirr, material.rayMirr)) 
            shaderElement.appendChild(valueElement)
        
        
    def writeHeader(self):
        doc = self.doc
        html = doc.createElementNS("http://www.w3.org/1999/xhtml", "html")
        html.setAttribute("xmlns", "http://www.w3.org/1999/xhtml")
        doc.appendChild(html)
        
        head = doc.createElement("head")
        html.appendChild(head)
        
        link = doc.createElement("link")
        link.setAttribute("rel", "stylesheet")
        link.setAttribute("type", "text/css")
        link.setAttribute("media", "all")
        link.setAttribute("href", "http://www.xml3d.org/xml3d/script/xml3d.css")
        head.appendChild(link)
        
        body = doc.createElement("body")
        html.appendChild(body)
        header = doc.createElement("h1")
        header.appendChild(doc.createTextNode(Blender.Get('filename')))
        body.appendChild(header)
        
        div = doc.createElement("div")
        body.appendChild(div)

        return div
    
    
    def writeScripts(self, parent):
        location = "http://www.xml3d.org/xml3d/script/"
        scripts = ["xml3d.js"]
      
        for script in scripts:
            scriptElem = self.doc.createScriptElement(None, location + script, "text/javascript")
            parent.appendChild(scriptElem)
      
    def writeLight(self, obj, parent):
        group = self.doc.createGroupElement()
        group.setTransform("#t_%s" % obj.name)
        parent.appendChild(group)
        
        
        light = self.doc.createLightElement();
        light.setShader("#ls_%s" % obj.getData(name_only=1))
        group.appendChild(light)
        
    def writeSceneGraph(self, parent):
        for obj in self.scene.objects:
            
            if obj.restrictRender:
                continue
            
            if (obj.getType() == 'Mesh'):
                self.writeMeshObject(obj, parent)
            if (obj.getType() == 'Lamp'):
                self.writeLight(obj, parent)
    
    def writeViews(self, parent):
        if not self.scene.objects.camera:
            view = self.doc.createViewElement("defaultView")
            parent.appendChild(view)
        else:
            for obj in bpy.data.objects:
                if (obj.getType() == 'Camera'):
                    view = self.doc.createViewElement(obj.name);
                    view.setPosition("%.6f %.6f %.6f" % (obj.LocX, obj.LocY, obj.LocZ))
                    quat = obj.mat.rotationPart().toQuat()
                    rot = quat.axis
                    view.setOrientation("%.6f %.6f %.6f %.6f" % (rot[0], rot[1], rot[2], quat.angle * DEG2RAD))
                    parent.appendChild(view)
      
   
        
    def write(self, scene):
      
        self.doc = XML3DDocument();
        self.scene = scene
        renderData = scene.getRenderingContext()

      
        print('--> START: Exporting XML3D to %s' % self.filename)
        start_time = Blender.sys.time()
        try:
            out = open(self.filename, 'w')
        except:
            print('ERROR: Could not open %s' % self.filename)
            return False
      
      
        parent = self.writeHeader()
    
        world = scene.world
        
        view = "#defaultView"
        if scene.objects.camera:
            view = "#"+scene.objects.camera.name
        
        xml3dElem = self.doc.createXml3dElement(activeView_ = view)
        xml3dElem.setAttribute("xmlns", "http://www.xml3d.org/2009/xml3d")
        if self.annotatePhysics:
            xml3dElem.setAttribute("xmlns:physics", "http://www.xml3d.org/2010/physics")
            if world:
                xml3dElem.setAttribute("physics:gravity", "0 %.6f 0" % (-world.gravity))
        
        
        style = "width: %ipx; height: %ipx;" % (renderData.sizeX, renderData.sizeY)
        if world:
            bgColor = world.getHor()
            style += " background-color:rgb(%i,%i,%i);" % (bgColor[0] * 255, bgColor[1] * 255, bgColor[2] * 255)
        
        
        xml3dElem.setAttribute("style", style)
    
        parent.appendChild(xml3dElem)
      
        self.writeMainDef(xml3dElem)
      
        self.writeViews(xml3dElem)
      
        self.writeSceneGraph(xml3dElem)
           
        self.writeScripts(parent)
    
        self.doc.writexml(out, " ", " ", "\n", "UTF-8")
    
        out.close()
        print('--> END: Exporting XML3D. Duration: %.2f' % (Blender.sys.time() - start_time))
        return

def export_gui(filename):
    exporter = xml3d_exporter(filename, True)
    scene = Blender.Scene.GetCurrent()
    exporter.write(scene)

def XML3DExportGUI():
    defaultFileName = Blender.Get('filename') + ".xhtml"
    defaultFileName = defaultFileName.replace('.blend', '')
    Window.WaitCursor(1)
    Window.FileSelector(export_gui, 'Export XML3D', defaultFileName)
    Window.WaitCursor(0)
  
if "cl" in sys.argv:
    #print("From command line")
    exporter = xml3d_exporter("C:/tmp/test.xhtml", False)
    scene = Blender.Scene.GetCurrent()
    exporter.write(scene)
    Blender.Quit()
else:
    XML3DExportGUI()


