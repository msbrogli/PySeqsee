# Copyright (C) 2011, 2012  Abhijit Mahabal
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this
# program.  If not, see <http://www.gnu.org/licenses/>

"""Class to set up and start running the application based on flags."""

from farg.core.controller import Controller
from farg.core.run_mode import batch, gui, single, sxs
from farg.core.stopping_conditions import StoppingConditions
from farg.core.ui.batch_ui import BatchUI
from farg.core.ui.gui import GUI
import logging
import logging.config
import os.path
import sys
import farg_flags

class Main:
  """The Base class for the Main class of an application.

  Based on flags, it sets up the appropriate run mode (which start GUIs if needed).
  It also does a sanity check on flags and creates certain directories if needed.
  """
  #: Class to use for running in GUI mode.
  run_mode_gui_class = gui.RunModeGUI  # Not a constant as thought by pylint: disable=C6409
  #: Class to use for running in Batch mode.
  run_mode_batch_class = batch.RunModeBatch  # Not a constant pylint: disable=C6409
  #: Class to use for running in SxS mode.
  run_mode_sxs_class = sxs.RunModeSxS  # Not a constant pylint: disable=C6409
  #: Class to use for running in single mode.
  run_mode_single_run_class = single.RunModeSingle  # Not a constant pylint: disable=C6409

  #: GUI class to use for the tkinter GUI.
  #: Subclasses of Main can override this, probably with a subclass of its value here.
  gui_class = GUI  # Not a constant pylint: disable=C6409
  #: Batch UI class to use for running in non-interactive mode. It should be able to handle
  #: any questions that may be generated by its codelets.
  #: Subclasses of Main can override this, probably with a subclass of its value here.
  batch_ui_class = BatchUI  # Not a constant pylint: disable=C6409

  #: The controller runs the show by scheduling codelets to run.
  #: Subclasses of Main can override this, probably with a subclass of its value here.
  controller_class = Controller  # Not a constant pylint: disable=C6409

  #: In batch and sxs modes, the inputs over which to run are specified in a file.
  #: These will be converted to flags passed to individual runs. An input reader should
  #: be specified for the file to series of flags conversion.
  #: These will usually be a subclass of ReadInputSpec.
  input_spec_reader_class = None  # Not a constant pylint: disable=C6409

  #: A mapping between stopping condition names and their implmentation (which is a funtion
  #: that takes a controller and returns a bool).
  stopping_conditions_class = StoppingConditions  # Not a constant pylint: disable=C6409

  #: Name of application. Must be provided by the derivative class.
  application_name = None  # Not a constant pylint: disable=C6409

  def __init__(self, unprocessed_flags):
    """Parses and sanity checks flags, plus creates the run_mode object."""
    if not self.application_name:
      print('application_name not set. The subclass of farg.core.Main that you called'
            'should have over-ridden this. See farg.apps.seqsee.run_seqsee.py for an'
            'example')
      sys.exit(1)

    #: The mode for the program (gui, batch, sxs, etc). This is an instance of
    #: :py:class:`~farg.core.run_mode.RunMode`.
    self.run_mode = None

    #: If not none, this is a function is a stopping condition for stopping the app.
    self.stopping_condition_fn = None

    self.flags = unprocessed_flags
    farg_flags.FargFlags = self.flags
    self.ProcessFlags()

  def VerifyPersistentDirectoryPath(self):
    """Verify (or create) the persistent directory."""
    directory = self.flags.persistent_directory
    if not directory:
      homedir = os.path.expanduser('~')
      if not os.path.exists(homedir):
        print ('Could not locate home directory for storing LTM files.'
               'You could explicitly specify an existing directory to use by using'
               'the flag --ltm_directory. Quitting.')
        sys.exit(1)
      pyseqsee_home = os.path.join(homedir, '.pyseqsee')
      if not os.path.exists(pyseqsee_home):
        print('Creating directory for storing pyseqsee files: %s' % pyseqsee_home)
        os.mkdir(pyseqsee_home)
      directory = os.path.join(pyseqsee_home, self.application_name)
    if not os.path.exists(directory):
      print('Creating directory for storing persistent files for the %s app: %s' %
            (self.application_name, directory))
      os.mkdir(directory)
    self.flags.persistent_directory = directory

  def VerifyLTMPath(self):
    """Create a directory for ltms unless flag provided. If provided, verify it exists."""
    if self.flags.ltm_directory:
      if not os.path.exists(self.flags.ltm_directory):
        print ("LTM directory '%s' does not exist." % self.flags.ltm_directory)
        sys.exit(1)
    else:
      self.VerifyPersistentDirectoryPath()
      self.flags.ltm_directory = os.path.join(self.flags.persistent_directory, 'ltm')
      if not os.path.exists(self.flags.ltm_directory):
        print('Creating directory for storing ltms: %s' % self.flags.ltm_directory)
        os.mkdir(self.flags.ltm_directory)

  def VerifyStatsPath(self):
    """Create directory for batch stats unless provided. If provided, verify it exists."""
    if self.flags.stats_directory:
      if not os.path.exists(self.flags.stats_directory):
        print ('Stats directory "%s" does not exist.' % self.flags.stats_directory)
        sys.exit(1)
    else:
      self.VerifyPersistentDirectoryPath()
      self.flags.stats_directory = os.path.join(self.flags.persistent_directory, 'stats')
      if not os.path.exists(self.flags.stats_directory):
        print('Creating directory for storing stats: %s' % self.flags.stats_directory)
        os.mkdir(self.flags.stats_directory)

  def VerifyStoppingConditionSanity(self):
    """Verify that stopping conditions are specified only in modes where they make sense."""
    run_mode_name = self.flags.run_mode
    stopping_condition = self.flags.stopping_condition
    if run_mode_name == 'gui':
      # There should be no stopping condition.
      if stopping_condition:
        print('Stopping condition does not make sense with GUI.')
        sys.exit(1)
    else:  # Verify that the stopping condition's name is defined.
      if self.flags.stopping_condition and self.flags.stopping_condition != 'None':
        stopping_conditions_list = self.stopping_conditions_class.StoppingConditionsList()
        if self.flags.stopping_condition not in stopping_conditions_list:
          print('Unknown stopping condition %s. Use one of %s' %
                (self.flags.stopping_condition, stopping_conditions_list))
          sys.exit(1)
        else:
          self.stopping_condition_fn = (
            self.stopping_conditions_class.GetStoppingCondition(self.flags.stopping_condition))
      else:
        self.stopping_condition_fn = ''

  def CreateRunModeInstance(self):
    """Create a Runmode instance from the flags."""
    run_mode_name = self.flags.run_mode
    if run_mode_name == 'gui':
      return self.run_mode_gui_class(controller_class=self.controller_class,
                                     ui_class=self.gui_class)
    elif run_mode_name == 'single':
      return self.run_mode_single_run_class(controller_class=self.controller_class,
                                            ui_class=self.batch_ui_class,
                                            stopping_condition_fn=self.stopping_condition_fn)
    else:
      if not self.flags.input_spec_file:
        print('Runmode --run_mode=%s requires --input_spec_file to be specified' %
              run_mode_name)
        sys.exit(1)
      input_reader = self.input_spec_reader_class()  # pylint: disable=E1102
      input_spec = list(input_reader.ReadFile(self.flags.input_spec_file))
      print(input_spec)
      if run_mode_name == 'batch':
        return self.run_mode_batch_class(controller_class=self.controller_class,
                                         input_spec=input_spec)
      elif run_mode_name == 'sxs':
        return self.run_mode_sxs_class(controller_class=self.controller_class,
                                       input_spec=input_spec)
      else:
        print('Unrecognized run_mode %s' % run_mode_name)
        sys.exit(1)

  def ProcessFlags(self):
    """Called after flags have been read in."""
    if self.flags.debug_config:
      logging.config.fileConfig(self.flags.debug_config)
      
    if self.flags.debug:
      numeric_level = getattr(logging, self.flags.debug.upper(), None)
      if not isinstance(numeric_level, int):
        print('Invalid log level: %s' % self.flags.debug)
        sys.exit(1)
      logging.basicConfig(level=numeric_level, format='%(levelname)s:%(message)s')
      logging.getLogger().setLevel(numeric_level)  # To override based on --debug flag
      logging.debug("Debugging turned on")

    self.ProcessCustomFlags()

    if self.flags.input_spec_file:
      # Check that this is a file and it exists.
      if not os.path.exists(self.flags.input_spec_file):
        print ("Input specification file '%s' does not exist. Bailing out." %
               self.flags.input_spec_file)
        sys.exit(1)
      if not os.path.isfile(self.flags.input_spec_file):
        print ("Input specification '%s' is not a file. Bailing out." %
               self.flags.input_spec_file)
        sys.exit(1)

    self.VerifyStoppingConditionSanity()
    self.VerifyPersistentDirectoryPath()
    self.VerifyLTMPath()
    self.VerifyStatsPath()
    self.run_mode = self.CreateRunModeInstance()


  def ProcessCustomFlags(self):
    """Apps can override this to process app-specific flags."""
    pass

  def Run(self):
    """Start the run.

    For Batch mode and SxS, this means running the app several times, whereas for gui mode
    this means launching a UI.
    """
    self.run_mode.Run()
