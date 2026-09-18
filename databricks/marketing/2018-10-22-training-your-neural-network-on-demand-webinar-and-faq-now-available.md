# Training your Neural Network: On-Demand Webinar and FAQ Now Available!

- Source: https://www.databricks.com/blog/2018/10/22/training-your-neural-network-on-demand-webinar-and-faq-now-available.html
- Published: 2018-10-22
- Authors: Denny Lee, Cyrielle Simeone
- Categories: platform, solutions, engineering, data-science-machine-learning
- Images: 3 total, 0 extracted as architecture

[Try this notebook in Databricks](https://pages.databricks.com/rs/094-YMS-629/images/Keras%20MNIST%20CNN%20%28Part%202%29.html)

On October 9th, we hosted a live webinar—[Training your Neural Network](https://www.slideshare.net/databricks/training-neural-networks-122043775)—on Data Science Central with Denny Lee, Technical Product Marketing Manager at Databricks. This is the second webinar of a free deep learning fundamental series from Databricks.

In this webinar, we covered the principles for training your neural network including activation and loss functions, batch sizes, data normalization, and validation datasets.

In particular, we talked about:

- Hyperparameter tuning, learning rate, backpropagation and the risk of overfitting
- Optimization algorithms, including Adam
- Convolutional Neural Networks and why they are so effective for image classification and object recognition

We demonstrated some of these concepts using Keras (TensorFlow backend) on Databricks, and here is a link to our notebook to get started today:

- [Keras MNIST CNN (Part 2)](https://pages.databricks.com/rs/094-YMS-629/images/Keras%20MNIST%20CNN%20%28Part%202%29.html)
- [Keras MNIST CNN (Part 1)](https://pages.databricks.com/rs/094-YMS-629/images/Keras%20MNIST%20CNN.html)

You can still watch Part 1 below and now register to Part 3 where we will dive more into Convolutional Neural Networks and how to use them:

If you’d like free access [Databricks Unified Analytics Platform](https://www.databricks.com/product/data-lakehouse) and try our notebooks on it, you can access a [free trial here](https://www.databricks.com/try-databricks).

Toward the end, we held a Q&A, and below are all the questions and their answers, grouped by topics.

### Fundamentals

**Q****: What is the difference between a perceptron and an artificial neural network, neuron, or node?**

A perceptron is a single layer artificial neural network (ANN) utilized as a binary classifier.  As neuron is typically associated with the biological neuron, often the term node is used to reference an artificial neuron within an ANN.

**Q: How do you decide the number of hidden layers for your [Artificial Neural Network](https://www.databricks.com/glossary/artificial-neural-network) (ANN)? Is it common that the ANN needs to be four layers by four neurons?  **

As noted in [Introduction to Neural Networks On Demand Webinar and FAQ Now Available](https://www.databricks.com/blog/2018/10/01/introduction-to-neural-networks-on-demand-webinar-and-faq-now-available.html), while there are general rules of thumb on your starting point (e.g. start with one hidden layer and expand accordingly, number of input nodes is equal to the dimension of features, etc.), the key thing is that you will need to test.  That is, train your model and then run the test and/or validation runs against that model to understand the accuracy (higher is better) and loss (lower is better).

**Q: What is the difference between a Recurrent Neural Network when compared to Convolutional Neural Networks as discussed in the webinar?**

Convolutional Neural Networks are well designed for image data but have the limitation that they are designed for fixed-size input and output vectors (e.g. MNIST digit image as the input and one of 10 digits as the possible output).  Recurring Neural Networks (RNNs) overcome this limitation because they work against sequences of vectors. A great blog on the topic of RNNs is [The Unreasonable Effectiveness of Recurrent Neural Networks](http://karpathy.github.io/2015/05/21/rnn-effectiveness/).

### Activation Functions

**Q: In the webinar, did you suggest that you should never use the Sigmoid activation function?  **

Specifically, the quote within the webinar (slide 15) is from [CS231N Convolutional Neural Networks for Visual Recognition](https://cs231n.github.io/neural-networks-1/) course at Stanford by Andrej Karparthy (currently Director of AI at Tesla):

*“What neuron type should I use?” Use the ReLU non-linearity, be careful with your learning rates and possibly monitor the fraction of “dead” units in a network. If this concerns you, give Leaky ReLU or Maxout a try. Never use sigmoid. Try tanh, but expect it to work worse than ReLU/Maxout.*

Generally, this is a good rule of thumb as your starting point on what activation functions you should be using. The focus should be more about using ReLU, Leaky ReLU, or Maxout activation functions as they often result in higher accuracy and lower loss.  For more information, please refer to [Introduction to Neural Networks](https://vimeo.com/292246874/3dafe96108?mkt_tok=eyJpIjoiWTJZd01tTTFOR1JqTmpOayIsInQiOiJYMkdLRWE0QmRcL0VsYkdTTDM2Z2lRQzV0MVZxaTVKS3pzRVMyclwvWnFhcnY5RWxSR3BTRWN4UUpNSFF0S0l3bWlJODBBOEtQWnBKY21ud2NzMEp0QktJNnJRS2FXTW9yblh5d1g0Z2lrVUVwb2htTVJRcUxlNnFKZWtESVExbFwvYSJ9) where we dive deeper into activation functions.

### Optimization

**Q: Why use Stochastic Gradient Descent (SGD) as your optimization if there may be better optimizers such as ADADelta?**

In this webinar, we focused on the specific area of image classification and it can be seen that using Adadelta optimizer converged much faster than other optimizations - for this scenario.  Also alluded to in the webinar, there are other variables in play: activation functions, neural network architecture, usage scenarios, etc. As there is still more research to come on this topic, there will be new strategies and optimization techniques to try out.

**Q: When should we use gradient boosting (e.g. Adaptive Boosting or AdaBoost) instead of Artificial Neural Networks Gradient Descent?  When can we use AdaBoost instead of ADADelta? **

Adaptive Boosting (AdaBoost) is the adaptive technique of gradient boosting as described in the paper [A Decision-Theoretic Generalization of On-Line Learning](https://www.face-rec.org/algorithms/Boosting-Ensemble/decision-theoretic_generalization.pdf)[and an Application to Boosting](https://www.face-rec.org/algorithms/Boosting-Ensemble/decision-theoretic_generalization.pdf).  In general, the idea is that you would boost weak learners (learners that do only slightly better than random chance) by filtering out data so that the weak learners could more easily handle the dataset.  While the current research points toward ANNs being simpler and faster to converge, it is also important to note that this is far from a definitive statement. For example, while the paper Comparison of machine learning methods for classifying mediastinal lymph node metastasis of non-small cell lung cancer from 18F-FDG PET/CT images notes that CNNs are more convenient, the paper Learning Deep ResNet Blocks Sequentially using Boosting Theory notes that their BoostResNet algorithm is more computationally efficient than compared to end-to-end back propagation in deep ResNet.  While these are two very disparate papers, the important call out is that there is still more important work being done in this exciting field.

**Q: How can you adapt your model when working with skewed data?**

Within the context of convolutional neural networks, the issue being described here is a class imbalance problem.  A great paper on this topic is a systematic study of the class imbalance problem in convolutional neural networks.  In general, it calls out the impact of class imbalance is quite high and oversampling is the current dominant mechanism to address it.

## Resources

- [Machine Learning 101](https://medium.com/onfido-tech/machine-learning-101-be2e0a86c96a)
- [Andrej Karparthy’s ConvNetJS MNIST Demo](https://cs.stanford.edu/people/karpathy/convnetjs/demo/mnist.html)
- [What is back propagation in neural networks?](https://www.quora.com/What-is-back-propagation-in-neural-networks)
- CS231n: Convolutional Neural Networks for Visual Recognition
  - [Course Notes](https://cs231n.github.io/) | [YouTube](https://www.youtube.com/watch?v=g-PvXUjD6qg&list=PLlJy-eBtNFt6EuMxFYRiNRS07MCWN5UIA)
  - With particular focus on [CS231n: Lecture 7: Convolution Neural Networks](https://www.youtube.com/watch?v=LxfUGhug-iQ)
- [Neural Networks and Deep Learning](http://neuralnetworksanddeeplearning.com/index.html)
- [TensorFlow](https://www.tensorflow.org/)
- [Deep Visualization Toolbox](https://www.youtube.com/watch?v=AgkfIQ4IGaM)
- [Back Propagation with TensorFlow](http://blog.aloni.org/posts/backprop-with-tensorflow/)
- [TensorFrames: Google TensorFlow with Apache Spark](https://www.databricks.com/session/tensorframes-deep-learning-with-tensorflow-on-apache-spark)
- [Integrating deep learning libraries with Apache Spark](https://www.slideshare.net/databricks/integrating-deep-learning-libraries-with-apache-spark)
- [Build, Scale, and Deploy Deep Learning Pipelines with Ease](https://www.databricks.com/blog/2017/09/06/build-scale-deploy-deep-learning-pipelines-ease.html)
