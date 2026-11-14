# Assignment 3: Bank Customer Churn -- Neural Network Classifier

## Problem statement
Given a bank customer, build a neural network-based classifier that can
determine whether they will leave or not in the next 6 months. Dataset
description: an open-source Kaggle dataset of 10,000 sample points with 14
distinct features such as CustomerId, CreditScore, Geography, Gender, Age,
Tenure, Balance, etc.

## Approach
- **Model**: `sklearn.neural_network.MLPClassifier` (a multi-layer
  perceptron -- a real feedforward neural network with backpropagation),
  used INSTEAD OF TensorFlow/Keras to avoid a multi-hundred-MB install for
  one script. Swap in `keras.Sequential` with equivalent Dense layers if a
  grader specifically requires Keras.
- Features are standardized (`StandardScaler`) first: gradient-based
  training is sensitive to the relative scale of inputs, unlike a
  tree-based model.
- **Evaluation**: accuracy score and confusion matrix. Churn is a minority
  class, so the confusion matrix matters more than raw accuracy (a model
  that always predicts "stays" can still look accurate). Precision and
  recall for churn are read off its second row and column.

## Implementation notes
- `RowNumber`, `CustomerId` and `Surname` are identifiers, not features, so
  they are dropped.
- `pd.get_dummies(..., drop_first=True)` one-hot encodes the text columns
  `Geography` and `Gender`.
- The network has two hidden layers of 16 and 8 units. ReLU is the default
  activation of `MLPClassifier`.
- Result on the test set: accuracy 0.873, confusion matrix
  `[[1551, 42], [213, 194]]`. Churn precision is 194/236 = 0.82 and recall is
  194/407 = 0.48, so the model misses about half of the real churners.

## Dataset
The real Kaggle "Churn_Modelling.csv" (bank customer churn), 10,000
customers with CreditScore, Geography, Gender, Age, Tenure, Balance,
NumOfProducts, HasCrCard, IsActiveMember, EstimatedSalary and the `Exited`
churn label, saved locally at `data/Churn_Modelling.csv`.

## Viva prep

**Q: Why MLPClassifier instead of TensorFlow/Keras?**
A: It's a genuine feedforward neural network (backpropagation across
hidden layers), available in scikit-learn -- already a dependency here --
avoiding a much larger, separate TensorFlow install for one script.

**Q: Why does this script scale features but a Random Forest wouldn't need
to?**
A: Gradient-based training is sensitive to each feature's relative scale
(it affects gradient magnitudes per weight); tree splits are invariant to
the scale of any single feature.

**Q: Why might accuracy alone be misleading for churn prediction?**
A: Churners are a minority class -- a model predicting "no churn" for
everyone can still score high accuracy while catching zero churners, which
is exactly what precision/recall on the churn class expose.

**Q: What is the role of the ReLU activation function between layers?**
A: It introduces non-linearity; without it, stacking linear layers would
collapse into a single linear transform and the network couldn't model
non-linear churn relationships in the data.
