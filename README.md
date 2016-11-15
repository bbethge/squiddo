# Squiddo
This is a bit of a mess.  `glut` seems to be the most advanced
branch, but I don’t know the differences between them anymore.
There is an alternate implementation in `python/` which should
be its own branch but instead is present in multiple branches.

The purpose of this project is to be a zooming file browser,
inspired by [Dasher] (http://www.inference.phy.cam.ac.uk/dasher/).
Click to enter zoom mode and an arrow will be drawn from the
center to your cursor indicating your “direction” of movement.
Vertical movement is regular scrolling, but horizontal movement
zooms in (to the right) and out (to the left).  Initially you
are at the root directory, so you had better go right (zoom in)
in order to see anything interesting.  Click again to exit zoom
mode and stop moving.

When I tested the `glut` branch, the C version segfaulted and
the Python version worked but with very light grey, almost
invisible text.
