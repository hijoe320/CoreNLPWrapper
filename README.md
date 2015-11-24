# CoreNLP_JPype_Wrapper
A JPype based Wrapper for Stanford CoreNLP

# Prerequisites
- JPype
- xml2json

# Example
```
# example params
params = {
    "ner.model.7class": "ner_yahoo.ser.gz",
    "annotators": "tokenize,ssplit,pos,lemma,ner"
}

ca = CorenlpAnnotator(
    # path to stanford nlp folder
    corenlp_classpath="/path/to/stanford-corenlp-full-2015-04-20",
    memory_size="3g",
    # for OSX EI Capitan installed with Oracle JDK
    jvm_path="/Library/Java/JavaVirtualMachines/jdk1.8.0_66.jdk/Contents/Home/jre/lib/jli/libjli.dylib",
)

# will start an annotator
ca.run()

print(ca.annotate("Hello World!"))

# call this to stop the annotator
ca.stop()
```
