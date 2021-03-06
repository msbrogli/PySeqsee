Update the GUI
================

The inputs do not yet show up in the UI. Let's fix that.

The UI is implemented in :py:mod:`tkinter`, and all components are drawn on a :py:class:`tkinter.Canvas`.
Depending on the selected view (something you can change using the menu at the top left), the full
canvas or only a fraction of it is alloted to the workspace view.

The default view (generated by "farg create") just displays a "hello, world" message. To produce
something more useful, we will modify the file farg/apps/bongard/gui/workspace_view.py, which
currently contains the placeholder method ReDraw::

  class WorkspaceView(ViewPort):
    def ReDraw(self, controller):
      """Redraw the workspace if it is being displayed. This is not called otherwise.

      The attributes that you have access to include self.width, self.height and a method to
      convert this widget's coordinates to the full canvas coordinates.
      """
      workspace = controller.workspace

      # EDIT-ME: You'd want to add something real here.
      x, y = self.CanvasCoordinates(10, 10)
      self.canvas.create_text(x, y, text='Hello, World!', anchor=NW)

We will replace this method to display the items in two columns, leaving space for other details we
may need to display later. We will space items out so that the bigger set uses the full height of the
canvas window::

  class WorkspaceView(ViewPort):
    def ReDraw(self, controller):
      workspace = controller.workspace

      bigger_set_size = max(len(workspace.left_items), len(workspace.right_items))
      space_per_element = self.height / (bigger_set_size + 1)

      x_offset_for_left_set = self.width * 0.2
      x_offset_for_right_set = x_offset_for_left_set + self.width / 2

      for idx, element in enumerate(workspace.left_items):
        x, y = self.CanvasCoordinates(x_offset_for_left_set, (idx + 0.5) * space_per_element)
        self.canvas.create_text(
            x, y, text='%d' % element.magnitude,
            font='-adobe-helvetica-bold-r-normal--28-140-100-100-p-105-iso8859-4',
            fill='#0000FF')

      for idx, element in enumerate(workspace.right_items):
        x, y = self.CanvasCoordinates(x_offset_for_right_set, (idx + 0.5) * space_per_element)
        self.canvas.create_text(
            x, y, text='%d' % element.magnitude,
            font='-adobe-helvetica-bold-r-normal--28-140-100-100-p-105-iso8859-4',
            fill='#00FF00')

The methods to pay attention to here include:

* self.height and self.width, which are the sizes of the part of the canvas available for the
  workspace. This amount can change depending on the view: it is possible to display the workspace,
  coderack, and stream at once, for example.
* The top left corner has the virtual co-ordinate (0, 0), and the bottom right has (self.width, self.height)
* The method CanvasCoordinates() converts the virtual coordinates to those on the actual canvas.
