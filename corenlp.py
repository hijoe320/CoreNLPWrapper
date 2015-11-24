# 

import os
import logging
import jpype as jp
import json
from glob import glob
from xml2json import xml2dict
from multiprocessing import Process, Event


class CorenlpAnnotator(object):
    def __init__(
        self, corenlp_classpath=None, memory_size="3g", jvm_path=None, **params
    ):
        """
        :param corenlp_classpath: (optional) path to StanfordCoreNLP jars, if 
            not set, will use environment variable ``CORENLP`` as default value.
        :param memory_size: (optional) maximum memory to be used for JVM, 
            default value is ``3g``
        :param jvm_path: (optional) path to jvm, if not set, will call 
            ``jpype.getDefaultJVMPath()`` to get it.
        :param **params: (optional) parameters for StanfordCoreNLP, can use same 
            params as in corenlp java command line, for example:
            ``outputFormat="XML"`` or if need to set ``ner.model=ner.ser.gz``,
            will need to wrap as a python dict:
        ... params = {
        ...     "ner.model": "ner.ser.gz",
        ...     "annotators": "tokenize,ssplit,pos,lemma,ner"
        ... }
        ... annotator = CorenlpAnnotator(**params)
        """
        if corenlp_classpath is None:
            if "CORENLP" in os.environ:
                corenlp_classpath = os.environ["CORENLP"]
            else:
                raise Exception("Classpath of CoreNLP not found, define CORENLP as a system env variable.")
        jars = [
            "stanford-corenlp-?.?.?-models.jar",
            "stanford-corenlp-?.?.?.jar",
            "joda-time.jar",
            "jollyday.jar",
            "xom.jar"
        ]
        self.corenlp_classpath = []
        for jar in jars:
            self.corenlp_classpath += (
                glob(os.path.join(corenlp_classpath, jar))
            )
        self.corenlp_classpath = ':'.join(self.corenlp_classpath)
        self.memory_size = memory_size
        self.jvm_path = jvm_path or jp.getDefaultJVMPath()
        self.params = params or {}
        self.params["outputFormat"] = "xml"
        self._daemon = Process(
            target=self._daemon_loop,
            name="CorenlpAnnotator-Daemon"
        )
        self._corenlp = None
        self._exit = Event()

    @property
    def is_alive(self):
        return self._daemon.is_alive()
    
    def run(self):
        if self._daemon.is_alive():
            return
        jp.startJVM(
            self.jvm_path, "-Xmx{0}".format(self.memory_size),
            "-Djava.class.path={0}".format(self.corenlp_classpath)
        )
        Properties = jp.JClass('java.util.Properties')
        StanfordCoreNLP = jp.JPackage('edu').stanford.nlp.pipeline.StanfordCoreNLP
        self._props = Properties()
        for p in self.params:
            self._props.setProperty(p, self.params[p])
        self._corenlp = StanfordCoreNLP(self._props)
        self._daemon.daemon = True
        self._daemon.start()

    def stop(self):
        jp.shutdownJVM()
        self._exit.set()

    def __del__(self):
        self.stop()

    def _daemon_loop(self):
        self._exit.wait()
        logging.info('CorenlpAnnotator Daemon exit')

    def annotate(self, text, to_json=True):
        if not self.is_alive:
            self.run()
        annotation = self._corenlp.process(text)
        StringWriter = jp.JClass("java.io.StringWriter")
        writer = StringWriter()
        self._corenlp.xmlPrint(annotation, writer)
        xml = unicode(writer.toString())[103:]
        if to_json:
            d = self.parse_corenlp_xml(xml)
            d["raw"] = text
            return d
        else:
            return xml

    @staticmethod
    def parse_corenlp_xml(xml):
        d = xml2dict(xml)["root"]["document"]
        d["sentences"] = d["sentences"]["sentence"]
        if isinstance(d["sentences"], dict):
            d["sentences"] = [d["sentences"]]
        for i in range(len(d["sentences"])):
            d["sentences"][i]["tokens"] = d["sentences"][i]["tokens"]["token"]
            if isinstance(d["sentences"][i]["tokens"], dict):
                d["sentences"][i]["tokens"] = [d["sentences"][i]["tokens"]]
            for token in d["sentences"][i]["tokens"]:
                token["begin"] = token.pop("CharacterOffsetBegin")
                token["end"] = token.pop("CharacterOffsetEnd")
        return d
        
  
if __name__ == "__main__":
    # example params
    params = {
        "ner.model.7class": "ner_yahoo.ser.gz",
        "annotators": "tokenize,ssplit,pos,lemma,ner"
    }
    ca = CorenlpAnnotator(
        # path to stanford nlp
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
