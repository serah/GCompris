#  gcompris - intro_gravity.py
#
# Copyright (C) 2003, 2008 Bruno Coudoin
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, see <http://www.gnu.org/licenses/>.
#
# intro_gravity activity.
import gtk
import gtk.gdk
import gcompris
import gcompris.utils
import gcompris.skin
import gcompris.anim
import goocanvas
import pango
import gcompris.bonus
import gobject
from gcompris import gcompris_gettext as _

class Gcompris_intro_gravity:
  """Empty gcompris python class"""


  def __init__(self, gcomprisBoard):
    print "intro_gravity init"

    # Save the gcomprisBoard, it defines everything we need
    # to know from the core
    self.gcomprisBoard = gcomprisBoard
    self.gcomprisBoard.level=1
    self.gcomprisBoard.sublevel=1
    self.gcomprisBoard.number_of_sublevel=1
    self.gcomprisBoard.maxlevel = 3

    # Needed to get key_press
    gcomprisBoard.disable_im_context = True

  def start(self):
    print "intro_gravity start"

    # Set the buttons we want in the bar
    gcompris.bar_set(0)


    # Create our rootitem. We put each canvas item in it so at the end we
    # only have to kill it. The canvas deletes all the items it contains
    # automaticaly.
    self.rootitem = goocanvas.Group(parent =
                                    self.gcomprisBoard.canvas.get_root_item())

    #set initial background
    gcompris.set_background(self.gcomprisBoard.canvas.get_root_item(),"intro_gravity/solar_system.svgz")

    #Load the solar system image
    svghandle = gcompris.utils.load_svg("intro_gravity/solar_system.svgz")
    self.selection = goocanvas.Svg(
      parent = self.rootitem,
      svg_handle = svghandle,
      svg_id = "#selected"
      )

    #connect the selected label to the next screen
    self.selection.connect("button_press_event", self.set_level)
    gcompris.utils.item_focus_init(self.selection, None)

    self.text = goocanvas.Text(parent=self.rootitem,
      x = 400,
      y = 400,
      fill_color = "white",
      font = gcompris.skin.get_font("gcompris/title"),
      text = _("The Solar System"))

  def game(self):
    self.rootitem = goocanvas.Group(parent =
                                    self.gcomprisBoard.canvas.get_root_item())

    gcompris.utils.item_focus_remove(self.selection, None)
    self.text.remove()

    goocanvas.Text(
      parent = self.rootitem,
      x=400.0,
      y=100.0,
      text=_("Mass is directly proportional to gravitational force"),
      font = gcompris.skin.get_font("gcompris/subtitle"),
      fill_color="white",
      anchor = gtk.ANCHOR_CENTER,
      alignment = pango.ALIGN_CENTER
      )

    # Set a background image
    gcompris.set_background(self.gcomprisBoard.canvas.get_root_item(),
                           "intro_gravity/background.svg")

    #Load the middle planet - Uranus
    middle = mid_planet(self.rootitem,self.level)

    #Load planet on the left (saturn) and it's slider
    self.planet_left = fixed_planet(self.rootitem,middle)
    self.planet_left.load_planet("saturn.png",45,160,1)


    #Planet on right (neptune) and it's slider
    self.planet_right = fixed_planet(self.rootitem,middle)
    self.planet_right.load_planet("neptune.png",660,165,2)

  def end(self):
    print "intro_gravity end"
    # Remove the root item removes all the others inside it
    self.rootitem.remove()


  def ok(self):
    print("intro_gravity ok.")


  def repeat(self):
    print 'repeat'


  #mandatory but unused yet
  def config_stop(self):
    pass

  # Configuration function.
  def config_start(self, profile):
    print("intro_gravity config_start.")

  def key_press(self, keyval, commit_str, preedit_str):
    utf8char = gtk.gdk.keyval_to_unicode(keyval)
    strn = u'%c' % utf8char

    print("Gcompris_intro_gravity key press keyval=%i %s" % (keyval, strn))

  def pause(self, pause):
    # When the bonus is displayed, it call us first with pause(1) and then with pause(0)
    # the game is won
    if pause == 0:
      self.set_level(1,2,3)

  def set_level(self,a,b,c):
    if self.gcomprisBoard.level == 1:
      self.level = 150
    elif self.gcomprisBoard.level == 2:
      self.level = 100
    elif self.gcomprisBoard.level == 3:
      self.level = 50
    self.game()

  def next_level(self):
      gcompris.bonus.display(gcompris.bonus.WIN,gcompris.bonus.TUX)
      self.end()
      self.gcomprisBoard.level += 1
      self.timer_on = False
      self.board_paused = 1

  def crash(self):
      self.end()
      self.board_paused = 1
      self.timer_on = False
      gcompris.bonus.display(gcompris.bonus.LOOSE,gcompris.bonus.TUX)
      self.board_paused = 1

class mid_planet(Gcompris_intro_gravity):
  """Class for moving planet in the middle"""

  def __init__(self,rootitem,level):
    self.rootitem = rootitem
    pixbuf = gcompris.utils.load_pixmap("intro_gravity/uranus.png")
    self.planet_mid = goocanvas.Image(
      parent = self.rootitem,
      pixbuf = pixbuf,
      height = 50,
      width = 50,
      x = 375,
      y = 198)

    #declaring variables
    self.velocity = 0
    self.old_force = None
    self.count = 0
    self.planet_right_mass = self.planet_left_mass = 1000
    self.timer_on = False
    self.level = level
    self.true = 2

  def move_planet(self,force,planet,planet_mass):
    self.timer()
    if planet == 1:
      self.planet_left_mass = planet_mass
    else:
      self.planet_right_mass = planet_mass

    x = self.planet_mid.get_bounds().x1
    position = x + self.velocity
    if position < 615 and position > 175:
      self.planet_mid.set_properties(x=position,y=198)
      self.check(force)
    else:
      self.crash()
      gobject.source_remove(self.t)

  def check(self,force):
    #if forces from both planets are equal then velocity does not change
    if force == 'equal':
      self.velocity = self.last_velocity
      self.old_force = 'equal'

    #if there is no change in force applied then increase velocity gradually
    elif self.old_force == force:
      self.true = 2
      self.count += 1
      if self.count == self.level or self.velocity == 0:
        self.true = 1
        self.count = 0

    #incase of change in forces, change direction and velocity according to force
    elif self.old_force != force:
      self.last_velocity = self.velocity
      if force == 'left':
        self.velocity = -1
      elif force == 'right':
        self.velocity = 1
      self.old_force = force

    gobject.timeout_add(30,self.force)

  #check force
  def force(self):
    if self.planet_right_mass == self.planet_left_mass:
      self.move_planet('equal',1,self.planet_left_mass)

    elif self.planet_right_mass > self.planet_left_mass:
      if self.true == 1:
        self.velocity +=1
      self.move_planet('right',2,self.planet_right_mass)

    else:
      if self.true == 1:
        self.velocity -=1
      self.move_planet('left',1,self.planet_left_mass)

  def timer(self):
    if self.timer_on == False:
      self.t = gobject.timeout_add(10000,self.next_level)
      self.timer_on = True


class fixed_planet:
  """ Fixed planets """

  def __init__(self,rootitem,mid_instance):
    self.mid = mid_instance
    self.rootitem = rootitem

  def load_planet(self,planet_image,x,y,planet):
    self.planet_ = planet
    image = "intro_gravity/"+planet_image
    pixbuf = gcompris.utils.load_pixmap(image)
    self.planet = goocanvas.Image(
      parent = self.rootitem,
      pixbuf=pixbuf,
      height=120,
      width=120,
      x=x,
      y=y)

    if self.planet_ == 1:
      points_line = goocanvas.Points([(27,190),(27,270)])
    else:
      points_line = goocanvas.Points([(788,190),(788,270)])

    self.scale_slider= slider(self,points_line) #scale line

class slider:
  """ class for scale slider"""

  def __init__(self,planet_instance,points):
    self.planet_instance = planet_instance
    line = goocanvas.Polyline(
      parent = planet_instance.rootitem,
      points=points,
      stroke_color="grey",
      width=2.0)
    self.planet_mass = 1000

    if planet_instance.planet_ == 1:
      points_bar = goocanvas.Points([(21,247),(33,247)])
      button_x = 9
    else:
      points_bar = goocanvas.Points([(782,247),(794,247)])
      button_x = 770

    self.sliding_bar(points_bar)
    self.decrease_button(button_x)
    self.increase_button(button_x)

  def increase_button(self,x):
    pixbuf = gcompris.utils.load_pixmap("/intro_gravity/plus.png")
    button = goocanvas.Image(
      parent = self.planet_instance.rootitem,
      pixbuf = pixbuf,
      x = x,
      y = 175
      )

    if self.planet_instance.planet_ == 1:
      translate_x = -8
      x_bar = 21
      force = 'left'
    else:
      translate_x = -63
      x_bar = 782
      force = 'right'

    button.connect("button_press_event",self.set_mass,1.1,translate_x,-20,500,1,force)
    button.connect("button_press_event",self.move_bar,x_bar,-8,1)

  def decrease_button(self,x):
    pixbuf = gcompris.utils.load_pixmap("intro_gravity/minus.png")
    button = goocanvas.Image(
      parent = self.planet_instance.rootitem,
      pixbuf = pixbuf,
      x = x,
      y = 250
      )
    if self.planet_instance.planet_ == 1:
      translate_x = 10
      x_bar = 21
      force = 'right'
    else:
      translate_x = 78
      x_bar = 782
      force = 'left'
    button.connect("button_press_event",self.set_mass,0.9,translate_x,25,-500,2,force)
    button.connect("button_press_event",self.move_bar,x_bar,8,2)

  def sliding_bar(self,points):
    self.bar = goocanvas.Polyline(
      parent = self.planet_instance.rootitem,
      points=points,
      stroke_color="grey",
      line_width=5.0)

  def move_bar(self,a,b,c,x,y,button):
    y_old = self.bar.get_bounds().y1
    if (y_old > 207 and button ==1) or (y_old < 244 and button ==2):
      y_new = int(y_old + y)
      gcompris.utils.item_absolute_move(self.bar,x,y_new)

  def set_mass(self,a,b,c,scale,x,y,mass,button,force):
    if (self.planet_mass < 3500 and button ==1) or (self.planet_mass > 1000 and button ==2):
      self.planet_instance.planet.scale(scale,scale)
      self.planet_instance.planet.translate(x,y)
      self.planet_mass += mass

    self.planet_instance.mid.move_planet(force,self.planet_instance.planet_,self.planet_mass)
