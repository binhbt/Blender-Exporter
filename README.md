XML3D exporter for Blender
==========================

Version: DEV_VERSION

This archive contains the XML3D exporter for Blender. It uses the API
of Blender up to version 2.49. The new Blender Python API of 
versions > 2.5 is not (yet) supported.

For more information on Blender visit: http://www.blender.org/
For more information on XML3D visit: http://www.xml3d.org/

License
-------

The Blender XML3D exporter is released under GPL license. See source
code for details.


Install
-------

Locate the xml3d_exporter.py file in the scripts folder of your Blender
installation. For information on how to install scripts, see:

	http://wiki.blender.org/index.php/Doc:Manual/Extensions

After successful installation, an XML3D entry will appear in the `File->Export` menu.
If it does not appear, though you copied the script to the correct script folder, you
might have to refresh the menu entries: 'Scripts->Update menus'

Usage
-----

Export your scene to xhtml and open it with an XML3D capable Browser. That's all!
BTW, the exporter includes some scripts to render the scene also with WebGL, thus
try it in a WebGL-enabled Browser.


TODOs
-----

* Export animations
* Menu for exporter options
* Export physics annotations

Contact
-------
DFKI, Saarbrücken
Email: kristian.sons@dfki.de








  
