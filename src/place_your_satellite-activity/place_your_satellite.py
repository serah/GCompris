#  gcompris - place_your_satellite.py
#
# Copyright (C) 2012 Bruno Coudoin and Matilda Bernard
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
# place_your_satellite activity.
import gtk
import gtk.gdk
import gcompris
import gcompris.utils
import gcompris.skin
import gcompris.bonus
import goocanvas
import pango
import cairo
import math
import gobject

from gcompris import gcompris_gettext as _

class Gcompris_place_your_satellite:
  """Empty gcompris python class"""


  def __init__(self, gcomprisBoard):
    # Save the gcomprisBoard, it defines everything we need
    # to know from the core
    self.gcomprisBoard = gcomprisBoard

    # Needed to get key_press
    gcomprisBoard.disable_im_context = True

  def start(self):
    # Create our rootitem. We put each canvas item in it so at the end we
    # only have to kill it. The canvas deletes all the items it contains
    # automaticaly.
    self.game_complete = False
    self.rootitem = goocanvas.Group(parent =
                                    self.gcomprisBoard.canvas.get_root_item())

    self.background = goocanvas.Image(
      parent = self.rootitem,
      pixbuf = gcompris.utils.load_pixmap("place_your_satellite/background.jpg"),
      x = 1,
      y = 1)

    self.earth = goocanvas.Image(
      parent = self.rootitem,
      pixbuf = gcompris.utils.load_pixmap("place_your_satellite/earth.png"),
      x = gcompris.BOARD_WIDTH/2 - 50,
      y = gcompris.BOARD_HEIGHT/2 - 50)

    self.instructions()
    self.satellite = Satellite(self, self.rootitem)
    speed = Speed(self.satellite, self.rootitem)
    mass = Mass(self, self.satellite, self.rootitem)


    # Set the buttons we want in the bar
    gcompris.bar_set(gcompris.BAR_REPEAT)
    gcompris.bar_location(2,-1,0.5)

  def end(self):
    # Remove the root item removes all the others inside it
    self.rootitem.remove()


  def ok(self):
    pass

  def repeat(self):
    self.game_complete = True
    self.end()
    gobject.timeout_add(5, self.start)

  #mandatory but unused yet
  def config_stop(self):
    pass

  # Configuration function.
  def config_start(self, profile):
    print("place_your_satellite config_start.")

  def key_press(self, keyval, commit_str, preedit_str):
    pass

  def pause(self, pause):
    pass

  def set_level(self, level):
    pass

  def instructions(self):
    # Ready button
    self.text = goocanvas.Text(
      parent = self.rootitem,
      x = 384,
      y = 103,
      fill_color = "white",
      anchor = gtk.ANCHOR_CENTER,
      alignment = pango.ALIGN_CENTER,
      text = _('1. Click anywhere on the screen to place the satellite'
               '\n at the required distance from the sun '
               '\n 2. Click on the satellite and drag the line to set'
               '\n the speed of the satellite'))
    self.text.connect('button_press_event', self.ready_event)
    bounds = self.text.get_bounds()
    gap = 20

    self.text_back = goocanvas.Rect(
      parent = self.rootitem,
      radius_x = 6,
      radius_y = 6,
      x = bounds.x1 - gap,
      y = bounds.y1 - gap,
      width = bounds.x2 - bounds.x1 + gap * 2,
      height = bounds.y2 - bounds.y1 + gap * 2,
      stroke_color_rgba = 0xFFFFFFFFL,
      fill_color_rgba = 0xCCCCCC44L)
    gcompris.utils.item_focus_init(self.text_back, None)
    gcompris.utils.item_focus_init(self.text, self.text_back)
    self.text_back.connect('button_press_event', self.ready_event)

  def ready_event(self, widget, target, event):
    self.text_back.props.visibility = goocanvas.ITEM_INVISIBLE
    self.text.props.visibility = goocanvas.ITEM_INVISIBLE
    self.background.connect("button_press_event", self.satellite.load_satellite)

class Satellite:
  """Satellite simulation"""


  def __init__(self, game, rootitem):
    self.rootitem = rootitem
    self.satellite_exists = False
    self.game = game
    self.step = 0
    self.mass = 800

  def start_event(self, widget, target, event=None):
    if event.type == gtk.gdk.BUTTON_PRESS:
      if event.button == 1:
        bounds = widget.get_bounds()
        self.pos_x = (bounds.x1+bounds.x2)/2
        self.pos_y = (bounds.y1+bounds.y2)/2
        self.line =goocanvas.Polyline(
          parent = self.rootitem,
          points = goocanvas.Points([(self.pos_x, self.pos_y),
                                     (event.x, event.y)]),
          stroke_color = 'white',
          line_cap = cairo.LINE_CAP_ROUND,
          line_width = 2.0
          )
        return True

    if event.type == gtk.gdk.MOTION_NOTIFY:
      if event.state & gtk.gdk.BUTTON1_MASK:
        self.line.set_properties(
          points = goocanvas.Points([(self.pos_x, self.pos_y),
                                     (event.x, event.y)])
          )

    if event.type == gtk.gdk.BUTTON_RELEASE:
      if event.button == 1:

        # Get the earth center
        earth_bounds = self.game.earth.get_bounds()
        earth_x = (earth_bounds.x1 + earth_bounds.x2)/2
        earth_y = (earth_bounds.y1 + earth_bounds.y2)/2

        # Get the satellite center
        sat_bounds = self.satellite.get_bounds()
        sat_x = (sat_bounds.x1 + sat_bounds.x2)/2
        sat_y = (sat_bounds.y1 + sat_bounds.y2)/2

        # Calc the distances from earth center to sat and to click
        sat_dist = math.sqrt(((earth_x - sat_x)**2) + ((earth_y - sat_y)**2))
        click_dist = math.sqrt(((earth_x - event.x)**2) + ((earth_y - event.y)**2))

        # Make the angle be linear in the range 0 -> 2*PI
        sat_add = 0 if sat_y > earth_y else math.pi
        if sat_y > earth_y:
          sat_angle = math.acos((sat_x - earth_x) / sat_dist)
        else:
          sat_angle = math.pi * 2 - math.acos((sat_x - earth_x) / sat_dist)

        # Make the angle be linear in the range 0 -> 2*PI
        if event.y > earth_y:
          click_angle = math.acos((event.x - earth_x) / click_dist)
        else:
          click_angle = math.pi * 2 - math.acos((event.x - earth_x) / click_dist)

        # Fix the 0 angle case
        if sat_angle > click_angle + math.pi:
          click_angle += math.pi * 2
        elif click_angle > sat_angle + math.pi:
          click_angle -= math.pi * 2

        revolution_direction = 1 if click_angle < sat_angle else -1

        # Set the step to make the satellite start where it is now
        self.step = sat_angle / (math.pi/180)

        # Pass the line lengh * direction
        self.initiate_movement(math.sqrt((((self.pos_x - event.x)**2)) +
                                         ((self.pos_y - event.y)**2)) *
                               revolution_direction)
        self.line.remove()
        return True
    return False

  def load_satellite(self, a, b, event=None):
    if self.satellite_exists == False:
      x = event.x - 12
      y = event.y - 12
      self.satellite = goocanvas.Image(
        parent = self.rootitem,
        pixbuf = gcompris.utils.load_pixmap("place_your_satellite/satellite.png"),
        x = x,
        y = y)
      self.satellite_exists = True
      self.satellite.connect('button_press_event',self.start_event)
      self.satellite.connect('button_release_event',self.start_event)
      self.satellite.connect('motion_notify_event',self.start_event)
      return False

  def initiate_movement(self, speed):
    # Calculate distance and set speed
    earth_bounds = self.game.earth.get_bounds()
    earth_x = (earth_bounds.x1 + earth_bounds.x2)/2
    earth_y = (earth_bounds.y1 + earth_bounds.y2)/2
    satellite_bounds = self.satellite.get_bounds()
    satellite_x = (satellite_bounds.x1 + satellite_bounds.x2)/2
    satellite_y = (satellite_bounds.y1 + satellite_bounds.y2)/2
    self.distance = math.sqrt( ((earth_x - satellite_x)**2)
                               + ((earth_y - satellite_y)**2) )

    self.orbital_speed = math.sqrt(self.mass/self.distance)
    self.speed = speed / 20.0
    if self.game.game_complete == False:
      gobject.timeout_add(30, self.calculate, earth_x, earth_y)

  def calculate(self, x_center, y_center):
    self.orbital_speed = math.sqrt(abs(self.mass/self.distance))
    difference = abs(self.speed) - self.orbital_speed
    if abs(difference) < 0.7:
      value = self.revolve(x_center, y_center)
      return value
    elif difference < 0:
      value = self.crash(x_center, y_center)
      return value
    else:
      value = self.fly_off(x_center, y_center)
      return value

  def revolve(self, x_center, y_center):
    if self.game.game_complete == False:
      self.step += self.speed
      radian = self.step * (math.pi/180)
      x_circle = x_center + math.cos(radian) * self.distance
      y_circle = y_center + math.sin(radian) * self.distance
      gcompris.utils.item_absolute_move(self.satellite, int(x_circle), int(y_circle))
      return True

  def crash(self, x_center, y_center):
    if self.distance > 45 + (self.mass/self.mass) * 20:
      self.step += self.speed + 1
      radian = self.step * (math.pi/180)
      x_circle = x_center + math.cos(radian) * self.distance
      y_circle = y_center + math.sin(radian) * self.distance
      gcompris.utils.item_absolute_move(self.satellite, int(x_circle), int(y_circle))
      self.distance -=3
      return True

    else:
      self.load_crash_image()

  def load_crash_image(self):
    bounds = self.satellite.get_bounds()
    self.satellite.remove()
    crash_image = goocanvas.Image(
      parent = self.rootitem,
      pixbuf = gcompris.utils.load_pixmap("place_your_satellite/crash.png"),
      x = bounds.x1,
      y = bounds.y1)

  def fly_off(self, x_center, y_center):
    if self.distance < 500:
      self.step += self.speed
      radian = self.step * (math.pi / 180)
      x_circle = x_center + math.cos(radian) * self.distance
      y_circle = y_center + math.sin(radian) * self.distance
      gcompris.utils.item_absolute_move(self.satellite, int(x_circle), int(y_circle))
      self.distance +=5
      return True
    else:
      self.message()

  def message(self):
    text = goocanvas.Text(
      parent = self.rootitem,
      x = 384,
      y = 103,
      fill_color = "white",
      anchor = gtk.ANCHOR_CENTER,
      alignment = pango.ALIGN_CENTER,
      text = _("Satellite not in orbit"))
    bounds = text.get_bounds()
    gap = 20

    back = goocanvas.Rect(
      parent = self.rootitem,
      radius_x = 6,
      radius_y = 6,
      x = bounds.x1 - gap,
      y = bounds.y1 - gap,
      width = bounds.x2 - bounds.x1 + gap * 2,
      height = bounds.y2 - bounds.y1 + gap * 2,
      stroke_color_rgba = 0xFFFFFFFFL,
      fill_color_rgba = 0xCCCCCC44L)

class Speed:
  """ Class dealing with speed and it's display"""

  def __init__(self,satellite_instance, rootitem):
    self.rootitem = rootitem
    self.satellite_instance = satellite_instance

    self.length = 130
    self.button_width = 20
    line = goocanvas.Polyline(
      parent = self.rootitem,
      points = goocanvas.Points( [(650, 500), (780, 500)] ),
      stroke_color = "grey",
      width = 2.0)

    text_speed = goocanvas.Text(
      parent = rootitem,
      x = (650 + 780)/2,
      y = 470,
      anchor = gtk.ANCHOR_CENTER,
      alignment = pango.ALIGN_CENTER,
      fill_color = "white",
      text = _("Speed"))

    back = goocanvas.Rect(
      parent = self.rootitem,
      radius_x = 6,
      radius_y = 6,
      x = 630,
      y = 460,
      width = 169,
      height = 59,
      stroke_color_rgba = 0xFFFFFFFFL,
      fill_color_rgba = 0x0000FF44L)

    slider_x = 650 + self.length / 2.0
    self.bar = goocanvas.Polyline(
      parent = self.rootitem,
      points = goocanvas.Points([(slider_x, 495),
                                 (slider_x, 505)]),
      stroke_color = "grey",
      line_width = 5.0)

    # This is the relative position of the scale from 0 to 1
    # 0 is the bottom
    self.scale_value = 0.5
    self.speed_button(650, 500, self.button_width, '-', -0.01)
    self.speed_button(780, 500, self.button_width, '+', 0.01)

  def speed_button(self, x, y, size, text, move):
    button = goocanvas.Rect(
      parent = self.rootitem,
      x = x - size / 2.0,
      y = y - size / 2.0,
      width = size,
      height =  size,
      line_width = 1.0,
      stroke_color_rgba= 0xCECECEFFL,
      fill_color_rgba = 0x333333FFL,
      radius_x = 15.0,
      radius_y = 5.0,
      )
    gcompris.utils.item_focus_init(button, None)

    text = goocanvas.Text(
      parent = self.rootitem,
      x = x,
      y = y,
      text = text,
      font = gcompris.skin.get_font("gcompris/subtitle"),
      fill_color = "white",
      anchor = gtk.ANCHOR_CENTER,
      alignment = pango.ALIGN_CENTER
      )
    gcompris.utils.item_focus_init(text, button)

    button.connect("button_press_event", self.move_bar, move)
    text.connect("button_press_event", self.move_bar, move)

  def move_bar(self, widget, target, event, move):
    self.scale_value += move
    # Take care not to bypass bounds
    if self.scale_value > 1.0:
      self.scale_value = 1.0
      return
    elif self.scale_value < 0.0:
      self.scale_value = 0.0
      return

    self.bar.translate(move * 2.5 * self.length / 4.0, 0);
    self.set_speed(move)

  def set_speed(self, change):
    self.satellite_instance.speed += change * 2

class Mass:
  """ Class dealing with mass and it's display"""

  def __init__(self, game, satellite_instance, rootitem):
    self.rootitem = rootitem
    self.game = game
    self.satellite_instance = satellite_instance

    self.length = 130
    self.button_width = 20
    line = goocanvas.Polyline(
      parent = self.rootitem,
      points = goocanvas.Points( [(650, 400), (780, 400)] ),
      stroke_color = "grey",
      width = 2.0)

    text_speed = goocanvas.Text(
      parent = rootitem,
      x = (650 + 780)/2,
      y = 370,
      anchor = gtk.ANCHOR_CENTER,
      alignment = pango.ALIGN_CENTER,
      fill_color = "white",
      text = _("Mass"))

    back = goocanvas.Rect(
      parent = self.rootitem,
      radius_x = 6,
      radius_y = 6,
      x = 630,
      y = 360,
      width = 169,
      height = 59,
      stroke_color_rgba = 0xFFFFFFFFL,
      fill_color_rgba = 0x0000FF44L)

    slider_x = 650 + self.length / 2.0
    self.bar = goocanvas.Polyline(
      parent = self.rootitem,
      points = goocanvas.Points([(slider_x, 395),
                                 (slider_x, 405)]),
      stroke_color = "grey",
      line_width = 5.0)

    self.scale_value = 0.5
    self.scale_earth(self.scale_value)
    self.mass_button(650, 400, self.button_width, '-', -0.01)
    self.mass_button(780, 400, self.button_width, '+', 0.01)

  def mass_button(self, x, y, size, text, move):
    button = goocanvas.Rect(
      parent = self.rootitem,
      x = x - size / 2.0,
      y = y - size / 2.0,
      width = size,
      height =  size,
      line_width = 1.0,
      stroke_color_rgba= 0xCECECEFFL,
      fill_color_rgba = 0x333333FFL,
      radius_x = 15.0,
      radius_y = 5.0,
      )
    gcompris.utils.item_focus_init(button, None)

    text = goocanvas.Text(
      parent = self.rootitem,
      x = x,
      y = y,
      text = text,
      font = gcompris.skin.get_font("gcompris/subtitle"),
      fill_color = "white",
      anchor = gtk.ANCHOR_CENTER,
      alignment = pango.ALIGN_CENTER
      )
    gcompris.utils.item_focus_init(text, button)

    button.connect("button_press_event", self.move_bar, move)
    text.connect("button_press_event", self.move_bar, move)

  def move_bar(self, widget, target, event, move):
    self.scale_value += move
    # Take care not to bypass bounds
    if self.scale_value > 1.0:
      self.scale_value = 1.0
      return
    elif self.scale_value < 0.0:
      self.scale_value = 0.0
      return

    self.bar.translate(move * 2.5 * self.length / 4.0, 0);
    self.scale_earth(self.scale_value)
    self.change_mass(move)

  def scale_earth(self, scale):
    self.scale = scale
    self.game.earth.set_transform(None)
    # Center it
    bounds = self.game.earth.get_bounds()
    self.game.earth.scale(self.scale_value + 0.5, self.scale_value + 0.5)
    (x, y) = self.rootitem.get_canvas().\
        convert_to_item_space(\
      self.game.earth,
      gcompris.BOARD_WIDTH/2 - 50 + ((bounds.x2 - bounds.x1) / 2.0 * -1) * self.scale + 0.5,
      gcompris.BOARD_HEIGHT/2 - 50 + ((bounds.y2 - bounds.y1) / 2.0 * -1) * self.scale + 0.5)
    self.game.earth.set_properties( x = x, y = y )

  def change_mass(self, change):
    if change == -0.01:
      self.satellite_instance.mass -= 25
    else:
      self.satellite_instance.mass += 25