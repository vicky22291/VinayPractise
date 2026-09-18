# Running Apache Spark GraphX algorithms on Library of Congress subject heading SKOS

- Source: https://www.databricks.com/blog/2015/04/14/running-spark-graphx-algorithms-on-library-of-congress-subject-heading-skos.html
- Published: 2015-04-14
- Authors: Bob DuCharme
- Categories: engineering, open-source, data-science-machine-learning
- Images: 1 total, 0 extracted as architecture

This is a guest post from Bob DuCharme. Original article appeared in: [http://www.snee.com/bobdc.blog/2015/04/running-spark-graphx-algorithm.html](http://www.snee.com/bobdc.blog/2015/04/running-spark-graphx-algorithm.html)

---

**Well, one algorithm, but a very cool one.**

Last month, in [Apache Spark and SPARQL; RDF Graphs and GraphX](http://www.snee.com/bobdc.blog/2015/03/spark-and-sparql-rdf-graphs-an.html), I described how Apache Spark has emerged as a more efficient alternative to MapReduce for distributing computing jobs across clusters. I also described how Spark's GraphX library lets you do this kind of computing on graph data structures and how I had some ideas for using it with RDF data. My goal was to use RDF technology on GraphX data and vice versa to demonstrate how they could help each other, and I demonstrated the former with a Scala program that output some GraphX data as RDF and then showed some SPARQL queries to run on that RDF.

Today I'm demonstrating the latter by reading in a well-known RDF dataset and executing GraphX's Connected Components algorithm on it. This algorithm collects nodes into groupings that connect to each other but not to any other nodes. In classic Big Data scenarios, this helps applications perform tasks such as the identification of subnetworks of people within larger networks, giving clues about which products or cat videos to suggest to those people based on what their friends liked.

The US Library of Congress has been working on their [Subject Headings](https://id.loc.gov/authorities/subjects.html) metadata since 1898, and it's available in SKOS RDF. Many of the subjects include "related" values; for example, you can see that the subject [Cocktails](https://id.loc.gov/authorities/subjects/sh85027617.html) has related values of [Cocktail parties](https://id.loc.gov/authorities/subjects/sh85027615.html) and [Happy hours](https://id.loc.gov/authorities/subjects/sh2009010761.html), and that Happy hours has related values of [Bars (Drinking establishments)](https://id.loc.gov/authorities/subjects/sh93000452.html), [Restaurants](https://id.loc.gov/authorities/subjects/sh85113249.html), and Cocktails. So, while it includes skos:related triples that indirectly link Cocktails to Restaurants, it has none that link these to the subject of [Space stations](https://id.loc.gov/authorities/subjects/sh85125961.html), so the Space stations subject is not part of the same Connected Components subgraph as the Cocktails subject.

After reading the Library of Congress Subject Header RDF into a GraphX graph and running the Connected Components algorithm on the skos:related connections, here are some of the groupings I found near the beginning of the output:

(You can find the [complete output here](http://snee.com/bobdc.blog/files/readLoCSH.out), a 565K file.) People working with RDF-based applications already know that this kind of data can help to enhance search. For example, someone searching for media about "Space stations" will probably also be interested in media filed under "Space colonies" and "Extraterrestrial bases". This data can also help other applications, and now, it can help distributed applications that use Spark.

## Storing RDF in GraphX data structures

First, as I mentioned in the earlier blog entry, GraphX development currently means coding with the Scala programming language, so I have been learning Scala. My old friend from XML days Tony Coates wrote A Scala API for RDF Processing, which takes better advantage of native Scala data structures than I ever could, and the [banana-rdf Scala library](https://github.com/banana-rdf/banana-rdf) also looks interesting, but although I was using Scala my main interest was storing RDF in Spark GraphX data structures, not in Scala particularly.

The basic Spark data structure is the Resilient Distributed Dataset, or RDD. The graph data structure used by GraphX is a combination of an RDD for vertices and one for edges. Each of these RDDs can have additional information; the Spark website's Example Property Graph includes (name, role) pairs with its vertices and descriptive property strings with its edges. The obvious first step for storing RDF in a GraphX graph would be to store predicates in the edges RDD, subjects and resource objects in the vertices RDD, and literal properties as extra information in these RDDs like the (name, role) pairs and edge description strings in the Spark website's Example Property Graph.

But, as I also wrote last time, a hardcore RDF person would ask [these questions](http://www.snee.com/bobdc.blog/2015/03/spark-and-sparql-rdf-graphs-an.html#id106263):

-

What about properties of edges? For example, what if I wanted to say that an xp:advisorproperty was an rdfs:subPropertyOf the Dublin Core property dc:contributor?

-

The ability to assign properties such as a name of "rxin" and a role of "student" to a node like 3L is nice, but what if I don't have a consistent set of properties that will be assigned to every node—for example, if I've aggregated person data from two different sources that don't use all the same properties to describe these persons?

The Example Property Graph can store these (name, role) pairs with the vertices because that RDD is declared as RDD[(VertexId, (String, String))]. Each vertex will have two strings stored with it; no more and no less. It's a data structure, but you can also think of it as a proscriptive schema, and the second bullet above is asking how to get around that.

I got around both issues by storing the data in three data structures—the two RDDs described above and one more:

-

For the vertex RDD, along with the required long integer that must be stored as each vertex's identifier, I only stored one extra piece of information: the URI associated with that RDF resource. I did this for the subjects, the predicates (which may not be "vertices" in the GraphX sense of the word, but damn it, they're resources that can be the subjects or objects of triples if I want them to), and the relevant objects. After reading the triple {  } from the Library of Congress data, the program will create three vertices in this RDD whose node identifiers might be 1L, 2L, and 3L, with each of the triple's URIs stored with one of these RDD vertices.

-

For the edge RDD, along with the required two long integers identifying the vertices at the start and end of the edge, each of my edges also stores the URI of the relevant predicate as the "description" of the edge. The edge for the triple above would be (1L, 3L, http://www.w3.org/2004/02/skos/core#related).

-

To augment the graph data structure created from the two RDDs above, I created a third RDD to store literal property values. Each entry stores the long integer representing the vertex of the resource that has the property, a long integer representing the property (the integer assigned to that property in the vertex RDD), and a string representing the property value. For the triple {   "Happy hours"} it might store (3L, 4L, "Happy hours"), assuming that 4L had been stored as the internal identifier for the skos:prefLabel property. To run the Connected Components algorithm and then output the preferred label of each member of each subgraph, I didn't need this RDD, but it does open up many possibilities for what you can do with RDF in an a Spark GraphX program.

## Creating a report on Library of Congress Subject Heading connecting components

After loading up these data structures (plus another one that allows quick lookups of preferred labels) my program below applies the GraphX Connected Components algorithm to the subset of the graph that uses the skos:related property to connect vertices such as "Cocktails" and "Happy hours". Iterating through the results, it uses them to load a hash map with a list for each subgraph of connected components. Then, it goes through each of these lists, printing the label associated with each member of each subgraph and a string of hyphens to show where each list ends, as you can see in the excerpt above.

I won't go into more detail about what's in my program because I commented it pretty heavily. (I do have to thank my friend Tony, mentioned above, for helping me past one point where I was stuck on a Scala scoping issue. Also, as I've warned before, my coding style will probably make experienced Scala programmers choke on their Red Bull. I'd be happy to hear about suggested improvements.)

After getting the program to run properly with a small subset of the data, I ran it on the 1 GB subjects-skos-2014-0306.nt file that I downloaded from the Library of Congress with its 7,705,147 triples. Spark lets applications scale up by giving you an infrastructure to distribute program execution across multiple machines, but the 8GB on my single machine wasn't enough to run this, so I used two grep commands to create a version of the data that only had the skos:related and skos:prefLabel triples. At this point I had a total of 439,430 triples. Because my code didn't account for blank nodes, I removed the 385 triples that used them, leaving 439,045 to work with in a 60MB file. This ran successfully and you can follow the link shown earlier to see the complete output.

## Other GraphX algorithms to run on your RDF data

[Other GraphX algorithms](https://spark.apache.org/docs/latest/graphx-programming-guide.html#graph-algorithms) besides Connected Components include Page Rank and Triangle Counting. [Graph theory](https://en.wikipedia.org/wiki/Graph_theory) is an interesting world, in which my favorite phrase so far is "[strangulated graph](https://en.wikipedia.org/wiki/Strangulated_graph)".

One of the greatest things about RDF and Linked Data technology is the growing amount of interesting data being made publicly available, and with new tools such as these algorithms to work with this data—tools that can be run on inexpensive, scalable clusters faster than typical Hadoop MapReduce jobs—there are a lot of great possibilities.

//////////////////////////////////////////////////////////////////
 // readLoCSH.scala: read Library of Congress Subject Headings into
 // Spark GraphX graph and apply connectedComponents algorithm to those
 // connected by skos:related property.

import scala.io.Source
 import org.apache.spark.SparkContext
 import org.apache.spark.SparkContext._
 import org.apache.spark.graphx._
 import org.apache.spark.rdd.RDD
 import scala.collection.mutable.ListBuffer
 import scala.collection.mutable.HashMap

object readLoCSH {

val componentLists = HashMap[VertexId, ListBuffer[VertexId]]()
 val prefLabelMap = HashMap[VertexId, String]()

def main(args: Array[String]) {
 val sc = new SparkContext("local", "readLoCSH", "127.0.0.1")

// regex pattern for end of triple
 val tripleEndingPattern = """\s*\.\s*$""".r
 // regex pattern for language tag
 val languageTagPattern = "@[\\w-]+".r

// Parameters of GraphX Edge are subject, object, and predicate
 // identifiers. RDF traditionally does (s, p, o) order but in GraphX
 // it's (edge start node, edge end node, edge description).

// Scala beginner hack: I couldn't figure out how to declare an empty
 // array of Edges and then append Edges to it (or how to declare it
 // as a mutable ArrayBuffer, which would have been even better), but I
 // can append to an array started like the following, and will remove
 // the first Edge when creating the RDD.

var edgeArray = Array(Edge(0L,0L,"http://dummy/URI"))
 var literalPropsTriplesArray = new Array[(Long,Long,String)](0)
 var vertexArray = new Array[(Long,String)](0)

// Read the Library of Congress n-triples file
 //val source = Source.fromFile("sampleSubjects.nt","UTF-8") // shorter for testing
 val source = Source.fromFile("PrefLabelAndRelatedMinusBlankNodes.nt","UTF-8")

val lines = source.getLines.toArray

// When parsing the data we read, use this map to check whether each
 // URI has come up before.
 var vertexURIMap = new HashMap[String, Long];

// Parse the data into triples.
 var triple = new Array[String](3)
 var nextVertexNum = 0L
 for (i \\s+") // split on "> "
 // Variables have the word "triple" in them because "object"
 // by itself is a Scala keyword.
 val tripleSubject = triple(0).substring(1) // substring() call
 val triplePredicate = triple(1).substring(1) // to remove " t.attr ==
 "http://www.w3.org/2004/02/skos/core#related")

// Find connected components of skosRelatedSubgraph.
 val ccGraph = skosRelatedSubgraph.connectedComponents()

// Fill the componentLists hashmap.
 skosRelatedSubgraph.vertices.leftJoin(ccGraph.vertices) {
 case (id, u, comp) => comp.get
 }.foreach
 { case (id, startingNode) =>
 {
 // Add id to the list of components with a key of comp.get
 if (!(componentLists.contains(startingNode))) {
 componentLists(startingNode) = new ListBuffer[VertexId]
 }
 componentLists(startingNode) += id
 }
 }

// Output a report on the connected components.
 println("------ connected components in SKOS \"related\" triples ------\n")
 for ((component, componentList) 1) { // don't bother with lists of only 1
 for(c
