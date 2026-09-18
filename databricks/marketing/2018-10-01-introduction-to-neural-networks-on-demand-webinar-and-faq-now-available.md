# Introduction to Neural Networks: On-Demand Webinar and FAQ Now Available!

- Source: https://www.databricks.com/blog/2018/10/01/introduction-to-neural-networks-on-demand-webinar-and-faq-now-available.html
- Published: 2018-10-01
- Authors: Denny Lee, Cyrielle Simeone
- Categories: platform, solutions, engineering, data-science-machine-learning
- Images: 3 total, 0 extracted as architecture

[Try this notebook in Databricks](https://pages.databricks.com/rs/094-YMS-629/images/Keras%20MNIST%20CNN.html)

On September 27th, we hosted a live webinar—[Introduction to Neural Networks](https://www.slideshare.net/databricks/introduction-to-neural-networks-122033415)—with Denny Lee, Technical Product Marketing Manager at Databricks. This is the first webinar of a free deep learning fundamental series from Databricks.

In this webinar, we covered the fundamentals of deep learning to better understand what gives neural networks their expressive power:

- the potential of deep learning and examples of possible applications
- the mathematical concept behind [artificial neural networks](https://www.databricks.com/glossary/artificial-neural-network) (ANN)
- the concepts of gradient-descent optimization, backpropagation, and activation functions

We demonstrated some of these concepts using Keras (TensorFlow backend) on Databricks, and here is a link to our notebook to get started today [MNIST demo using Keras CNN on Databricks](https://pages.databricks.com/rs/094-YMS-629/images/Keras%20MNIST%20CNN.html)

You can now register to Part 2 and Part 3 where we will continue to explore the power of Neural Networks, and dive more into best-practices to train your neural networks (from preparing your datasets to parameters tuning) as well as architecture examples of Convolutional Neural Networks:

If you’d like free access [Databricks Unified Analytics Platform](https://www.databricks.com/product/data-lakehouse) and try our notebooks on it, you can access a [free trial here](https://www.databricks.com/try-databricks).

Toward the end, we held a Q&A, and below are the questions and their answers, grouped by topics.

### Fundamentals

**Q: Which activation function is preferred? or which cases suit a particular activation function?**

Using ReLU as your activation function is a good starting point as noted in many neural networks samples Keras MNIST,  [TensorFlow CIFAR10 Pruning](https://github.com/tensorflow/tensorflow/blob/9590c4c32dd4346ea5c35673336f5912c6072bf2/tensorflow/contrib/model_pruning/examples/cifar10/cifar10_pruning.py), etc.).  Note that each activation function has its own strengths and weaknesses.  A good quote on activation functions from [CS231N](https://cs231n.github.io/neural-networks-1/) summarizes the choice well:

>  “What neuron type should I use?” Use the ReLU non-linearity, be careful with your learning rates and possibly monitor the fraction of “dead” units in a network. If this concerns you, give Leaky ReLU or Maxout a try. Never use sigmoid. Try tanh, but expect it to work worse than ReLU/Maxout.

**Q: On what basis do you select the number of layers and number of neurons in each layer?**

In general, the more layers and the number of units in each layer, the greater the capacity of the artificial neural network.  The key concern is you may run the risk over overfitting when your goal is to build a generalized model.

From a practical perspective, a good starting point is:

- The number of input units equals the dimension of features
- The number of output units equals the number of classes (e.g. in the MNIST dataset, there are 10 possible values represents digits (0...9) hence there are 10 output units
- Start with one hidden layer that is 2x the number of input units

A good reference is Andrew Ng’s [Coursera Machine Learning course](https://www.coursera.org/learn/machine-learning).

**Q: What is the ideal training and testing data split size for training deep learning models ?**

The split size for deep learning models isn’t that different from general rules of Machine Learning; using an 80/20 split is a good starting point.

### Architecture/Ecosystem

**Q: What type of Azure VM should you use to train neural networks (and how much memory)?**

A good starting point with would be to utilize clusters with GPU nodes (as of this writing, for Azure this would the N-series VMs) and enough memory to hold a size-able portion of the data.

 

### Deep Learning on Databricks

**Q: Does Databricks provides step by step tutorial which can help to develop some pilots using Artificial Neural Networks (ANN)?**

Yes, absolutely, we encourage you to get started with this notebook to explore the potential of ANN. As well, for more examples, refer to the Deep Learning sections of the Databricks Documentation ([AWS](https://docs.databricks.com/applications/machine-learning/train-model/deep-learning.html) | [Azure](https://docs.microsoft.com/en-us/azure/databricks/applications/machine-learning/train-model/deep-learning)).

 

 

## Additional Resources

- [Machine Learning 101](https://medium.com/onfido-tech/machine-learning-101-be2e0a86c96a)
- [Andrej Karparthy’s ConvNetJS MNIST Demo](https://cs.stanford.edu/people/karpathy/convnetjs/demo/mnist.html)
- [What is back propagation in neural networks?](https://www.quora.com/What-is-back-propagation-in-neural-networks)
- CS231n: Convolutional Neural Networks for Visual Recognition
  - [Course Notes](https://cs231n.github.io/) | [YouTube](https://www.youtube.com/watch?v=g-PvXUjD6qg&list=PLlJy-eBtNFt6EuMxFYRiNRS07MCWN5UIA)
  - With a particular focus on [CS231n: Lecture 7: Convolution Neural Networks](https://www.youtube.com/watch?v=LxfUGhug-iQ)
- [Neural Networks and Deep Learning](http://neuralnetworksanddeeplearning.com/index.html)
- [TensorFlow](https://www.tensorflow.org/)
