from django.db import models
from DRP.settings import MODEL_DIR

class ModelStats(models.Model):
  class Meta:
    app_label = "DRP"

  # Model Statistics
  confusion_table = models.TextField(default="{}")
  headers = models.TextField(default="[]")
  correct_vals = models.CharField("Correct Values", max_length=100,
                                  default="[\"3\",\"4\"]")

  # Model Descriptors
  title = models.CharField("Title", max_length=100, default="untitled")
  description = models.TextField(default="")

  # Model Status and Location
  filename = models.CharField("Filename", max_length=128,
                                          default=MODEL_DIR+"untitled.model")
  active = models.BooleanField("Active", default=True)
  datetime = models.DateTimeField(auto_now_add=True, blank=True)
  usable = models.BooleanField("Usable", default=True)

  # Available model types.
  library = models.CharField("Library", max_length=128, default="weka")
  tool = models.CharField("Tool", max_length=128, default="random forest")
  response = models.CharField("Response", max_length=128, default="outcome")

  def construct(self, title, data, description="", library="sklearn",
                                     tool="random forest", response="outcome",
                                     filename="", force=False,
                                     usable=True, active=True,
                                     preprocessor=None, postprocessor=None,
                                     splitter=None, debug=False):

    from DRP.fileFunctions import file_exists

    # Use a custom splitter-function if specified.
    if not splitter:
      from DRP.model_building.load_data import test_split as splitter

    # Make sure we can actually write the model file.
    if not filename:
      filename = "".join(filter(str.isalnum, title))
    filename += "__{}__{}".format(library, tool)
    self.filename = filename

    # Don't overwrite models unless "force=True" is specified.
    if file_exists(self.get_path()) and not force:
      message = "Model '{}' already exists: use 'force=True'".format(self.get_path())
      raise Exception(message)

    if force and debug:
      print "Forcing overwrite: {}".format(self.get_path())


    # Save the description and fields of this model.
    self.title = title
    self.description = description
    self.usable = usable
    self.active = active
    self.library = library
    self.response = response
    self.tool = tool
    self.filename = filename

    # If specified, pre-process the data.
    if preprocessor:
      if debug: print "Pre-processing..."
      data = preprocessor(data)

    headers = data.pop(0)

    # Split the data.
    if debug: print "Splitting data..."
    split_data = splitter(data, headers=headers)
    if debug:
      splits = {key:len(val) for key, val in split_data.items()}
      print "Splits: {}".format(splits)


    # If specified, post-process the data after splitting.
    if postprocessor:
      if debug: print "Post-processing..."
      split_data, headers = postprocessor(split_data, headers)

    # Save the headers now that the data has successfully been split.
    if self.response not in headers:
      raise Exception("Response '{}' not found in headers!".format(self.response))

    self.set_headers(headers)


    # Train/fit the model
    if debug: print "Training model..."
    self._train_model(split_data["train"])


    # Set the confusion table for a given data-set.
    if debug: print "Testing model..."
    self._test_model(split_data["test"])

    self.save()

    if debug: print "Complete!"
    return self


  def get_path(self):
    from DRP.settings import MODEL_DIR
    return MODEL_DIR + self.filename

  def get_headers(self):
    import json
    return json.loads(self.headers)



  def _separate_response(self, data):
    if len(data)==0:
      raise Exception("`data` cannot be empty!")

    headers = self.get_headers()
    resp = headers.index(self.response)

    preds = [[elem for i, elem in enumerate(row) if i!=resp] for row in data]
    resps = [row[resp] for row in data]

    return preds, resps


  def predict_bulk(self, predictors):
    if self.library == "weka":
      # TODO: Construct the predictors ARFF
      # TODO: Parse the result file
      # TODO: Return the results.
      pass


    elif self.library == "sklearn":
      model = self._load_model()
      return model.predict(predictors)

    else:
      raise Exception("Unknown library specified in predict_bulk!")


  def _load_model(self):
    from sklearn.externals import joblib

    if self.library == "sklearn":
      return joblib.load(self.get_path())

    else:
      raise Exception("Illegal model library specified! Aborting file-load!")

  def _make_confusion_table(self, guesses, responses):
    if len(guesses)==0 or len(responses)==0:
      raise Exception("Either `guesses` or `responses` is empty!")

    if not (len(guesses)==len(responses)):
      raise Exception("`guesses` and `responses` are of different sizes!")

    possible_vals = sorted(list(set(guesses+responses)))
    cm = {r1:{r2:0 for r2 in possible_vals} for r1 in possible_vals}

    for guess, response in zip(guesses, responses):
      cm[response][guess] += 1

    return cm


  def _test_model(self, data):
    predictors, responses = self._separate_response(data)

    if self.library=="weka":
      self._make_arff("test", data)

    guesses = self.predict_bulk(predictors)

    if self.library =="sklearn":
      guesses = map(int, guesses)
      responses = map(int, responses)

    cm = self._make_confusion_table(guesses, responses)
    self.set_confusion_table(cm)


  def _train_model(self, data):
    from DRP.model_building.sklearn_methods import get_model
    from DRP.fileFunctions import get_django_path
    from sklearn.externals import joblib
    import subprocess

    if self.library=="weka":
      arff_name = self._make_arff("train", data)
      move = "cd {}; ".format(get_django_path())
      command = "bash DRP/model_building/make_model.sh "
      args = "{} {}".format(self.get_path(), arff_name)
      subprocess.check_output(move+command+args, shell=True)

    elif self.library=="sklearn":
      model, description = get_model(self.tool)
      predictors, responses = self._separate_response(data)
      model.fit(predictors, responses)

      # Save the model to a file.
      joblib.dump(model, self.get_path())

    else:
      raise Exception("_train_model called with illegal library!")


  def _make_arff(self, key, data):
    from DRP.fileFunctions import createDirIfNecessary
    from DRP.model_building.model_methods import preface
    from DRP.settings import TMP_DIR

    createDirIfNecessary(TMP_DIR)
    full_name = "{}{}_{}.arff".format(TMP_DIR, self.filename, key)

    with open(full_name, "w") as f:
      header_content = preface(self.get_headers())
      f.write(header_content + "\n")
      for row in data:
        f.write(",".join([str(entry) for entry in row]) + "\n")

    return full_name


  def set_correct_vals(self, correct_list):
    import json
    if not correct_list:
      correct_list = ["4","3"]
    self.correct_vals = json.dumps(correct_list)
    self.save()


  def load_all_vals(self):
    return sorted(self.load_confusion_dict().keys())

  def load_correct_vals(self):
    import json
    return sorted(json.loads(self.correct_vals))

  def load_incorrect_vals(self):
    correct = set(self.load_correct_vals())
    all_vals = self.load_all_vals()
    return [val for val in all_vals if val not in correct]


  def check_usability(self):
    import os

    try:
      assert( len(self.load_all_vals()) > 0 )
      assert( len(self.load_correct_vals()) > 0 )
      assert( os.path.isfile(self.get_path()) )
      usable = True
    except:
      usable = False

    if usable!= self.usable:
      self.usable = usable
      self.save()

    return usable


  def set_headers(self, field_list):
    import json
    self.headers = json.dumps(field_list)
    self.save()


  def set_confusion_table(self, conf_json):
    import json
    self.confusion_table = json.dumps(conf_json)
    self.save()

  def graph_confusion_table(self):
    import matplotlib.pyplot as plt
    ticks = self.load_all_vals()

    raw_cm = self.load_confusion_table(normalize=False, headers=False)
    cm = [map(float,row) for row in raw_cm]

    plt.matshow(cm, cmap=plt.cm.OrRd)
    plt.colorbar()
    plt.ylabel('True')
    plt.xlabel('Predicted')
    plt.xticks(range(len(ticks)), ticks)
    plt.yticks(range(len(ticks)), ticks)

    if self.title:
      plt.title(self.title)

    plt.show()


  def load_confusion_dict(self):
    import json
    return json.loads(self.confusion_table)

  def load_confusion_table(self, normalize=True, headers=True):
    """
    Confusion Dict:
    Abstract Format:
    {
      "Actual Value": {"Predicted Val":amount, "Predicted Val2": amount2, ... }
      ...
    }

    Actual Format:
    {
      "1":{"1":#, "2":#, "3":#, "4":#},
      "2":{"1":#, "2":#, "3":#, "4":#},
      "3":{"1":#, "2":#, "3":#, "4":#},
      "4":{"1":#, "2":#, "3":#, "4":#},
    }

    Confusion Matrix:
            __Predicted___
      __    V1   V2   V3 ...
      A  V1 #    #    #
      c
      t  V2 #    #    #
      u
      a  V3 #    #    #
      l
      __ ...
    """

    try:
      confusion_dict = self.load_confusion_dict()
    except:
      return []

    values = sorted(confusion_dict.keys())

    matrix = [[""]+values] if headers else []

    denom = self.total() if normalize else 1

    for value in values:
      guess_dict = confusion_dict[value]
      row = [value] if headers else []
      row += [guess_dict[v]/denom if v in guess_dict else 0 for v in values]
      matrix.append(row)

    return matrix


  def count(self, normalize=False, guesses=None, actuals=None, ranges=True, false_guess=False):
    # Variable Setup
    conf_table = self.load_confusion_table(normalize=normalize)

    guess_headers = conf_table.pop(0)[1:] # Remove the empty cell in [0,0].
    actual_headers = [row.pop(0) for row in conf_table]

    if not actuals: actuals = actual_headers
    if not guesses: guesses = guess_headers

    c = 0

    for value in (actuals+guesses):
      if value not in guess_headers or value not in actual_headers:
        raise Exception("Value '{}' not found in confusion table!".format(value))

    for i, guess in enumerate(guess_headers):
      for j, actual in enumerate(actual_headers):
        if ranges:
          if false_guess:
            if actual in actuals and guess in guesses and actual not in guesses:
              c += conf_table[j][i]

          else:
            if actual in actuals and guess in guesses:
              c += conf_table[j][i]

        else:
          if false_guess:
            if actual!=guess and actual in actuals and guess in guesses:
              c += conf_table[j][i]

          else:
            if actual==guess and actual in actuals and guess in guesses:
              c += conf_table[j][i]

    return c


  def total(self):
    conf_table = self.load_confusion_dict()
    int_total = sum([int(val) for correct,guesses in conf_table.items()
                              for key,val in guesses.items()])
    return float(int_total)

  # Convenience Wrappers
  def true_positives(self, ranges=True, normalize=False):
    corrects = self.load_correct_vals()
    return self.count(guesses=corrects, actuals=corrects,
                      normalize=normalize, ranges=ranges)

  def true_negatives(self, ranges=True, normalize=False):
    incorrects = self.load_incorrect_vals()
    return self.count(guesses=incorrects, actuals=incorrects,
                      normalize=normalize, ranges=ranges)

  def false_positives(self, ranges=True, normalize=False):
    corrects = self.load_correct_vals()
    return self.count(guesses=corrects, false_guess=True,
                      normalize=normalize, ranges=ranges)

  def false_negatives(self, ranges=True, normalize=False):
    incorrects = self.load_incorrect_vals()
    return self.count(guesses=incorrects, false_guess=True,
                      normalize=normalize, ranges=ranges)


  def test_accuracy(self, ranges=True):
    denom = float(self.total())
    if denom:
      tp = self.true_positives(ranges=ranges)
      tn = self.true_negatives(ranges=ranges)
      return (tp + tn)/denom
    else:
      return 0

  def test_precision(self, ranges=True):
    tp = self.true_positives(ranges=ranges)
    fp = self.false_positives(ranges=ranges)
    denom = float(tp + fp)
    if denom:
      return tp/denom
    else:
      return 0

  def user_satisfaction(self):
    from DRP.models import Recommendation
    recs = Recommendation.objects.filter(model_version=self)
    if recs.exists():
      return recs.filter(nonsense=False).count()/float(recs.count())
    else:
      return 0

  def pvalue(self):
    #TODO: return the p-value for this model.
    return float("inf") #TODO: Not this.

  def pretty_stats(self, classes=None):
    print "Model: {}".format(self.title)
    print "Description: {}".format(self.description)
    raw = self.stats()
    for categorization, stat_dict in raw.items():
      print "{}-categorization:".format(categorization)
      for stat, val in stat_dict.items():
        print "\t{}: {}".format(stat, val)


  def stats(self, classes=None):
    tests = {
      "2": {
        "Test Size":self.total(),
        "Accuracy":self.test_accuracy(ranges=True),
        "Rate TP":self.true_positives(normalize=True, ranges=True),
        "Rate FP":self.false_positives(normalize=True, ranges=True),
        "Rate TN":self.true_negatives(normalize=True, ranges=True),
        "Rate FN":self.false_negatives(normalize=True, ranges=True),
        "Precision":self.test_precision(ranges=True),
        "User Satisfaction":self.user_satisfaction(),
      },
      "4": {
        "Test Size":self.total(),
        "Accuracy":self.test_accuracy(ranges=False),
        "Rate TP":self.true_positives(normalize=True, ranges=False),
        "Rate FP":self.false_positives(normalize=True, ranges=False),
        "Rate TN":self.true_negatives(normalize=True, ranges=False),
        "Rate FN":self.false_negatives(normalize=True, ranges=False),
        "Precision":self.test_precision(ranges=False),
        "User Satisfaction":self.user_satisfaction(),
      }
    }

    if classes:
      if type(classes) in {set, list}:
        tests = {key:val for key,val in tests if key in classes}
      else:
        tests = tests[classes]

    return tests


  def print_confusion_table(self, normalize=True):
    def truncate_floats(row):
      cleaned = []
      for elem in row:
        try:
          cleaned.append("{:.3f}".format(elem))
        except:
          cleaned.append(elem)
      return cleaned

    conf_table = self.load_confusion_table(normalize=normalize)
    if conf_table:
      heading = "(%)" if normalize else ""
      print "\t\t\tPredicted {}".format(heading)
      for row in conf_table:
        cleaned_row = map(str, truncate_floats(row) )
        print "\t"+"\t".join( cleaned_row )
    else:
      print "\t[ Confusion Matrix Unavailable ]"


  def print_model_info(self, prefix="\t"):
    print prefix+"Name: '{}'".format(self.title)
    print prefix+"Description: '{}'".format(self.description)
    print prefix+"Created: {}".format(self.datetime)
    print prefix+"Filename: '{}'".format(self.filename)
    print prefix+"Headers: '{}'".format(len(self.get_headers()))
    print prefix+"Correct Values: {}".format(self.load_correct_vals())

  def summary(self, pre="\t"):
    self.print_model_info()
    print ""
    self.print_confusion_table()
    print ""

    stats = self.stats().items()
    stats.sort(key=lambda tup: tup[0])
    for stat, key in stats:
      print "{}{}: {}".format(pre, stat, key)


  def __unicode__(self):
    return "Model {} (Active:{}; Usable:{})".format(self.datetime,
                                                    self.active,
                                                    self.usable)

  def __repr__(self):
    return self.__unicode__()



