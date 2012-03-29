from farg.stream import Stream
from farg.coderack import Coderack
from farg.util import Toss
from farg.codelet import Codelet
from farg.ltm.manager import LTMManager
from farg.exceptions import FargException
class Controller(object):
  """A controller is responsible for controlling the Coderack.
     The Coderack, in turn, by the action of codelets, marshals the various pieces of a space
     or of an entire application.  These pieces include the stream, the long-term memory, and
     any pieces added by subclasses (a workspace will typically be added).

     A controller provides the method 'Step'.  This does two things.  First, it may add
     routine codelets.  The controller's constructor specifies what codelets to add and with
     what likelihood.  If the Coderack is empty, the codelets are added regardless of the
     likelihood.  Second, a codelet is selected from the Coderack and executed.  This codelet
     may access the stream, the long-term memory, or the workspace and could even add other
     codelets which the next call to 'Step' may execute.
  """

  #: What type of stream is owned by the controller.
  stream_class = Stream
  #: What type of coderack is owned by the controller.
  coderack_class = Coderack
  #: What type of workspace is owned by the controller. With None, gets no workspace.
  workspace_class = None
  #: This is a list containing 3-tuples made up of (family, urgency, probability).
  #: The probability is ignored during a Step if the coderack is empty.
  routine_codelets_to_add = ()
  #: Name of LTM used by the controller. If None, no LTM is created.
  ltm_name = None

  def __init__(self, *, ui):
    #: The coderack.
    self.coderack = self.coderack_class()
    #: The stream.
    self.stream = self.stream_class(self)
    if self.ltm_name:
      #: LTM, if any
      self.ltm = LTMManager.GetLTM(self.ltm_name)
    else:
      self.ltm = None
    #: Number of steps taken
    self.steps_taken = 0
    #: The UI running this controller. May be a GUI or a Guided UI (which knows how to
    #: answer questions that'd normally be answered by a user in a GUI). Any subspace
    #: spawned by this space shall inherit the ui.
    self.ui = ui
    # Add any routine codelets...
    self._AddRoutineCodelets(force=True)

  def _AddRoutineCodelets(self, force=False):
    """Add routine codelets to the coderack.

       The codelets are added with a certain probability (specified in the third term of the
       tuple), but this can be over-ridden with force (or if the coderack is empty).

       In the Perl version, this was called 'background codelets'.
    """
    if self.coderack.IsEmpty():
      force = True
    if self.routine_codelets_to_add:
      for family, urgency, probability in self.routine_codelets_to_add:
        if force or Toss(probability):
          self.coderack.AddCodelet(Codelet(family, self, urgency))


  def Step(self):
    """Executes the next (stochastically chosen) step in the model."""
    self.steps_taken += 1
    if self.ltm:
      self.ltm._timesteps = self.steps_taken
    self._AddRoutineCodelets()
    if not self.coderack.IsEmpty():
      codelet = self.coderack.GetCodelet()
      try:
        codelet.Run()
      except FargException as e:
        self.HandleFargException(e)

  def RunUptoNSteps(self, n_steps):
    """Takes upto N steps. In these, it is possible that an answer is found and an exception
       raised.
    """
    for _ in range(n_steps):
      self.Step()

  def AddCodelet(self, *, family, urgency, arguments_dict):
    """Adds a codelet to the coderack."""
    codelet = Codelet(family=family, controller=self,
                      urgency=urgency, arguments_dict=arguments_dict)
    self.coderack.AddCodelet(codelet)