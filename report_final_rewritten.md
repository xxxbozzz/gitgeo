# Sign Language Recognition Using Deep Convolutional Neural Networks

## 1. Introduction

In this project, I built and compared several convolutional neural network models for recognising American Sign Language alphabet gestures. The data came from the Sign Language MNIST dataset, which provides 28 by 28 grayscale images covering 24 static hand signs from A to Y, with J and Z left out because those letters involve motion rather than a single pose (Datamunge, 2017).

Compared with building a production-ready recognition system, this project focuses more on understanding how architectural choices affect what a model actually learns. Because of this, I paid more attention to whether each design decision could be justified by evidence, rather than chasing the highest possible accuracy. The objective was not only to obtain high classification accuracy, but also to compare how architectural depth, regularisation, optimiser settings, and batch size affect generalisation on unseen test images.

The project runs three experiments. The first is a simple baseline with two convolutional blocks and ReLU activations. The second is a tuned version of that baseline with a slower learning rate and larger batch size, designed to test whether smoother gradient updates improve generalisation. The third is a deeper VGG-style network with batch normalisation, dropout, L2 regularisation, and global average pooling. The untouched Kaggle test set was kept aside throughout tuning, so the final numbers give a fair picture of how well each model generalises. The validation data was split only from the training CSV, using a stratified 85/15 split to preserve class proportions.

## 2. Data Loading and Preprocessing

The Kaggle CSV files were loaded with pandas. Each row contains one label and 784 pixel values. I reshaped the pixel columns into tensors of shape 28 by 28 by 1, preserving the grayscale channel, and divided all pixel values by 255 to bring them into the 0 to 1 range. This normalisation makes gradient-based optimisation more stable because no single input feature dominates the loss landscape, and the optimiser does not need to compensate for large raw pixel magnitudes.

The original labels use alphabet indices from 0 to 24, with class 9 missing because J was excluded from the dataset. I remapped them to a continuous 0 to 23 range so that sparse categorical cross-entropy could be used with a 24-unit softmax output layer directly. The mapping was retained so that final predictions could still be displayed as readable letters. The official training file contained 27,455 images and the test file contained 7,172 images. I used a stratified 85/15 split of the training file, producing 23,336 training images and 4,119 validation images. Stratification was important because it preserved class proportions across both sets. The test set was never touched during tuning, which keeps the final test accuracy as a fair estimate of generalisation.

I chose not to resize the images. The dataset already provides standardised 28 by 28 pixel inputs, and resizing would introduce interpolation artefacts without any benefit for the training process. For larger pre-trained networks such as ResNet or VGG16, resizing would be necessary to match their expected input dimensions. But for custom CNNs trained from scratch, the native resolution is perfectly suitable.

These preprocessing choices also make the experiments reproducible. A fixed random seed was used across NumPy, Python, TensorFlow, and the validation split. Reproducibility matters for this assignment because model comparisons are only meaningful when the data split and initial conditions are controlled. The same training, validation, and test arrays were reused across all three experiments, so differences in results can be attributed mainly to architecture and hyperparameter settings rather than accidental changes in data preparation.

Figure 1 shows that the training classes are reasonably balanced. No single letter dominates the dataset, so the model comparison is not skewed by one or two frequent classes.

![Figure 1: Training class distribution](figures/class_distribution.png)

## 3. CNN Architectures

The baseline CNN used two Conv2D layers with ReLU activation and He normal initialisation, each followed by max pooling. The output of the second pooling layer was flattened and passed through a dense layer, dropout, and a 24-class softmax classifier. I built it this way deliberately because a weak but functional baseline makes it easier to see whether adding complexity actually helps. This architecture had 423,448 parameters, most of which were in the dense layer after flattening.

The enhanced model used a VGG-style structure with three convolutional blocks. Each block contained two 3 by 3 convolutional layers, batch normalisation, a max pooling layer, and dropout. The filter counts increased from 32 to 64 to 128 across the blocks, allowing the model to learn progressively richer hand-shape features at each stage. L2 regularisation penalised overly large weights, while dropout reduced co-adaptation between features within the same block. Global average pooling replaced the large flattening layer, cutting the number of dense parameters substantially.

One thing that surprised me during the design process was the parameter count comparison. The enhanced model had only 307,832 parameters, significantly fewer than the baseline's 423,448, but it was deeper and performed substantially better on unseen data. The baseline wastes parameters because flattening a feature map before the dense layer creates many fully connected weights. The enhanced model instead allocates more of its capacity to convolutional layers, where weights are shared spatially. For image recognition, this is usually a better trade-off, because local patterns such as edges, finger contours, and palm boundaries can appear anywhere in the frame. A larger parameter count does not automatically mean a better model.

## 4. Training, Hyperparameter Tuning, and Results

All models used sparse categorical cross-entropy because each image has exactly one class label. Adam was used as the optimiser because it adapts learning rates per parameter and is reliable for CNN image classification tasks. ReLU was used in hidden layers because it trains efficiently with He initialisation, while softmax was used for the output layer to produce class probabilities. Early stopping and reduce-on-plateau callbacks were included to avoid unnecessary training epochs if validation loss stopped improving.

Accuracy, loss, precision, recall, and F1-score were all tracked because accuracy alone can hide class-specific weaknesses. Precision is useful when asking whether a predicted letter is trustworthy, while recall is useful when asking whether real examples of a letter are being missed. F1-score combines both, making it a stronger summary when some classes are harder than others. Training time was also recorded because a model that is only slightly more accurate may not be worthwhile if it is significantly slower.

The hyperparameter tuning compared learning rate, batch size, and architecture across three representative experiments. The search was deliberately bounded because training deeper CNNs is computationally expensive and the assignment emphasises justified comparison rather than exhaustive grid search. The results are summarised below.

| Model | LR | Batch | Epochs | Parameters | Val Acc | Test Acc | Test Loss | Time |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Enhanced VGG | 0.001 | 128 | 10 | 307,832 | 100.00% | 99.39% | 0.1107 | 307.5s |
| Baseline | 0.001 | 128 | 8 | 423,448 | 99.17% | 86.98% | 0.3885 | 39.5s |
| Tuned baseline | 0.0005 | 256 | 8 | 423,448 | 94.83% | 84.62% | 0.5294 | 41.7s |

In the early design, I had expected the tuned baseline to outperform the original version. A smaller learning rate and larger batch size usually help stability, but here the opposite happened. The tuned baseline reached only 84.62 percent test accuracy, lower than the faster baseline at 86.98 percent. I think the smaller updates combined with the larger batch size prevented the model from exploring the loss surface effectively, leaving it stuck in a worse region. The original baseline hit 99.17 percent validation accuracy but only 86.98 percent on the test set. This kind of gap usually means the model learned something about the training distribution that does not transfer to unseen examples.

The enhanced VGG-style CNN closed this gap almost entirely. It achieved 100.00 percent validation accuracy and 99.39 percent test accuracy, with a macro F1-score of 0.9939. It took about 7.8 times longer to train than the baseline, but the 12.4 percentage point improvement in test accuracy makes that cost worthwhile when generalisation is the primary goal.

Figure 2 complements the table by showing that the enhanced CNN converged rapidly and maintained low validation loss without a widening training-validation gap.

![Figure 2: Training and validation curves for enhanced VGG-style CNN](figures/training_curves_vgg_style_adam_lr1e-3_bs128.png)

## 5. Evaluation

The best model was evaluated using a confusion matrix, classification report, and sample predictions. The overall test accuracy was 99.39 percent, with a weighted F1-score of 0.9939. Most classes achieved near-perfect precision and recall, while the hardest classes were still strong performers.

| Class | Precision | Recall | F1-score | Support |
|---|---:|---:|---:|---:|
| G | 1.000 | 0.971 | 0.985 | 348 |
| H | 0.978 | 1.000 | 0.989 | 436 |
| I | 0.954 | 1.000 | 0.976 | 288 |
| T | 1.000 | 0.927 | 0.962 | 248 |
| X | 0.937 | 1.000 | 0.967 | 267 |
| Y | 1.000 | 0.958 | 0.978 | 332 |
| macro avg | 0.994 | 0.994 | 0.994 | 7172 |
| weighted avg | 0.994 | 0.994 | 0.994 | 7172 |

The confusion matrix showed that remaining errors were concentrated in visually similar signs. T was predicted as X 18 times, Y as I 14 times, and G as H 10 times. This is plausible because at 28 by 28 resolution, fingers in similar positions can be difficult to distinguish, and the model does not have access to colour or depth information to help it.

Figure 3 shows the confusion matrix, and Figure 4 provides labelled test image samples rather than only numerical scores. Most predictions are correct, and the few errors are consistent with subtle gesture similarities rather than random failure.

![Figure 3: Confusion matrix for enhanced VGG-style CNN](figures/confusion_matrix_best.png)

![Figure 4: Sample predictions from the test set](figures/sample_predictions_best.png)

## 6. Reflection and Limitations

The main limitation of this work is that Sign Language MNIST is a simplified static-image benchmark. Real sign-language recognition must handle live camera input, varied backgrounds, different skin tones, inconsistent lighting, hand scale variation, occlusion, motion blur, and different signers with different signing styles. It must also recognise dynamic signs such as J and Z, which are excluded from this dataset entirely. This project therefore demonstrates isolated ASL letter classification rather than usable sign-language translation.

The baseline models also highlight why validation accuracy alone can be misleading. The best baseline reached very high validation accuracy, but its test accuracy remained below 87 percent. This indicates that the official test set is harder or distributed differently from the validation split. The enhanced model generalised much better because its deeper convolutional blocks learned more robust spatial features, while batch normalisation, dropout, L2 regularisation, and global average pooling all contributed to reducing overfitting.

There are also broader considerations for any system that might build on this work. A practical assistive tool should not be evaluated only on benchmark accuracy. It should be tested with diverse users, should communicate uncertainty when the model is unsure rather than outputting a confident but wrong translation, and should be designed as a support tool rather than a replacement for human interpreters or fluent sign-language communication. These points limit how far the current results can be generalised, but they also show why robust hand-gesture recognition remains a valuable research direction.

Further work could explore residual architectures, stronger but realistic data augmentation, cross-validation, and signer-independent evaluation. A compact ResNet-style model would be a natural extension because residual connections help train deeper networks more reliably, as demonstrated by He et al. (2016). For a deployable assistive technology system, the next stage would be collecting real webcam data with diverse participants and extending the model to video sequences using CNN-LSTM or transformer-based temporal modelling.

## References

Datamunge. (2017). Sign Language MNIST. Kaggle. https://www.kaggle.com/datasets/datamunge/sign-language-mnist

He, K., Zhang, X., Ren, S., and Sun, J. (2016). Deep Residual Learning for Image Recognition. Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR), 770-778. https://doi.org/10.1109/CVPR.2016.90
