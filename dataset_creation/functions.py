import nltk
import random
from nltk.stem import WordNetLemmatizer, PorterStemmer
from pyUML import Graph, UMLClass

nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('wordnet')
nltk.download('omw-1.4')

lemmatizer = WordNetLemmatizer()

def get_all_tagged(text):
    text_token = nltk.sent_tokenize(text)
    all_tagged = []
    for token in text_token:
        wordsList = nltk.word_tokenize(token)
        tagged = nltk.pos_tag(wordsList)
        all_tagged.append(tagged)
    return all_tagged

def get_entities_attributes(all_tagged):
    entities = set()
    business_env = ["database", "record", "system", "information", "organization", "detail", "website"]
    noun_or_gerund  = ["NN", "NNS", "VBG"]
    lemmatizer = WordNetLemmatizer()
    for tagged in all_tagged:
        for i, word in enumerate(tagged):
            word_lem = lemmatizer.lemmatize(word[0])
            if word[1] in noun_or_gerund:
                if i > len(tagged):
                    if tagged[i+1][1] in noun_or_gerund:
                        next_word_lem = lemmatizer.lemmatize(tagged[i+1][0])
                        entities.add(word_lem + "_" + next_word_lem)
                elif tagged[i-1][1] in noun_or_gerund:
                    continue
                elif word_lem in business_env:
                    continue
                else:
                    entities.add(word_lem)
    
    attributes_noun_phrase_main = set()
    relationship_attributes = set()
    concept_attributes = set()
    verb = {"VB", "VBG", "VBD", "VBN", "VBP", "VBZ"}
    adjectives = {"JJ", "JJR", "JJS"}
    specific_indicators = {"type", "number", "date", "reference","no","code","volume","birth","id","address","name"}
    for tagged in all_tagged:
        for i, word in enumerate(tagged):
            #A1
            if word[1] == "JJ":
                attributes_noun_phrase_main.add(word[0])
            #A2
            if word[1] == "RB":
                if tagged[i-1][1] in verb and tagged[i+1][1] not in adjectives:
                    relationship_attributes.add(word[0])
            #A3
            if tagged[i][1] == "POS":
                concept_attributes.add(tagged[i-1][1])
                entities.discard(tagged[i-1][0])
                if tagged[i-2][0] == "and":
                    concept_attributes.add(tagged[i-3][0])
                    entities.discard(tagged[i-3][0])
            #A4
            if tagged[i][0] == "of":
                concept_attributes.add(tagged[i-1][0])
            if word[1] == "NN" or word[1] == "NNS":
                if tagged[i-1][1] == "IN":
                    if tagged[i-2][1] in verb:
                        concept_attributes.add(word[0])
                        entities.discard(word[0])
                        if i < len(tagged):
                            if tagged[i+1][0] == "and":
                                concept_attributes.add(tagged[i+2][0])
                                entities.discard(tagged[i+2][0])
            #A5
            if word[0] == "have" and tagged[i-1][0] == "to":
                concept_attributes.add(tagged[i+1][0])
                entities.discard(tagged[i+1][0])
            #A6
            if word[0] in specific_indicators:
                concept_attributes.add(word[0])
                if i < len(tagged):
                    if tagged[i+1][0] == "," and (tagged[i+2][1] == "NN" or "NNS"):
                        concept_attributes.add(tagged[i+2][0])
                        entities.discard(tagged[i+2][0])
                    elif tagged[i+1][1] == "NN" or "NNS":
                        concept_attributes.add(tagged[i+1][0])
                        entities.discard(tagged[i+1][0])
    return entities, concept_attributes

def get_entity(text, attribute, entities):
    lemmatizer = WordNetLemmatizer()
    words = nltk.word_tokenize(text)
    i = words.index(attribute)
    while i >= 0:
        word_lem = lemmatizer.lemmatize(words[i])
        if word_lem in entities:
            return word_lem
        i -= 1

def get_object(list,index):
    # lemmatizer = WordNetLemmatizer()
    obj='none'
    sub='none'

    for i in range(1,index+1):

        if obj!='none' : break

        if list[index-i][1] in ['NN','NNS','NNP','NNPS']:
            if list[index-i-1][1] not in ['NN','NNS','NNP','NNPS']:
                obj=list[index-i][0]
            else :
                obj=list[index-i-1][0]+'_'+list[index-i][0]
        elif list[index-i][1] == 'MD':
            if list[index-i-1][1] in ['NN','NNS','NNP','NNPS'] and list[index-i-2][1] in ['NN','NNS','NNP','NNPS'] :
                obj=list[index-i-2][0]+'_'+list[index-i-1][0]
            elif list[index-i-1][1] in ['NN','NNS','NNP','NNPS']:
                obj=list[index-i-1][0]

    for i in range(1,len(list)-index):
        if sub!='none' : break

        if list[index+i][1] in ['NN','NNS','NNP','NNPS']:
            if list[index+i+1][1] not in ['NN','NNS','NNP','NNPS']:
                sub=list[index+i][0]
            else :
                sub=list[index+i][0]+'_'+list[index+i+1][0]

        elif list[index+i][1] == 'DT':
            if list[index+i+1][1] in ['NN','NNS','NNP','NNPS'] and list[index+i+2][1] in ['NN','NNS','NNP','NNPS'] :
                sub=list[index+i+1][0]+'_'+list[index+i+2][0]
            elif list[index+i+1][1] in ['NN','NNS','NNP','NNPS']:
                sub=list[index+i+1][0]
    # return lemmatizer.lemmatize(obj), lemmatizer.lemmatize(sub)
    return obj, sub

def get_relations(all_tagged):
    stemmer = PorterStemmer()
    relationship = []
    inheritance = []
    object = []
    object_inh = []
    verb1=['include','involve','contain','comprise','embrace']
    verb2=['consist of','divided to']
    verb_not_rel=['described', 'identified']
    for tagged in all_tagged:
        for i, word in enumerate(tagged):
            word_stem = stemmer.stem(word[0])
            # check if word is a verb
            if word[0] == "is" and (tagged[i+1][0] == "a" or tagged[i+1][0] == "a"):
                inheritance.append(word[0]+' '+tagged[i+1][0])
                object_inh.append(get_object(tagged,i))
            elif word[1] in ['VB','VBD','VBG','VBN','VBP','VBZ'] and word[0] not in verb_not_rel:
                # check if next word is a preposition conjunction 
                if tagged[i+1][0] in ['by','in','on','to'] :
                    # A verb followed by a preposition  can indicate a relationship type
                    relationship.append(word[0]+' '+tagged[i+1][0])
                    object.append(get_object(tagged,i))
                # if a verb is in the following list {include, involve, consists of, contain, comprise, divided to, embrace},
                #  this indicate a relationship
                elif word_stem in verb1 :    
                    relationship.append(word[0])
                elif word_stem+' '+tagged[i+1][0] in verb2 :
                    relationship.append(word[0]+' '+tagged[i+1][0])
                    object.append(get_object(tagged,i))
                # check if verb is transitive
                elif tagged[i+1][1] in ['NN','NNS'] or tagged[i+1][1]=='DT' and tagged[i+2][1]in ['NN','NNS']:
                    #A transitive verb can indicate relationship type
                    relationship.append(word[0])
                    object.append(get_object(tagged,i))
    return inheritance, relationship, object, object_inh

def get_attribute_type(attribute):
    ints = ["no", "number", "num", "nb", "age"]
    for i in ints:
        if i in attribute:
            return "int"
    if "date" in attribute:
      return "date"
    else:
      return "string"

def text_to_uml(text):
    uml = {}
    all_tagged = get_all_tagged(text)
    entities, attributes = get_entities_attributes(all_tagged)
    for entity in entities:
        uml[entity] = []
    for attribute in attributes:
        uml[get_entity(text, attribute, entities)].append(attribute)
    inheritance, relationship, object, object_inh = get_relations(all_tagged)
    return uml, inheritance, relationship, object, object_inh

chars = "abcdefghijklmnopqrstuvwxyz0123456789"
def get_random_id(length):
    return ''.join((random.choice(chars) for _ in range(length)))

def graph_from_uml(uml, inheritance, relationship, object, object_inh):
    graph = Graph('pyUML')

    for rel, obj in zip(relationship, object):
        lemmatizer = WordNetLemmatizer()
        class1 = UMLClass(lemmatizer.lemmatize(obj[0]))
        graph.add_class(class1)
        class2 = UMLClass(lemmatizer.lemmatize(obj[1]))
        graph.add_class(class1)
        c1 = "0..*"
        c2 = "0..*"
        graph.add_association(class1, class2, label=rel, multiplicity_parent=c1, multiplicity_child=c2)

    for rel, obj in zip(inheritance, object_inh):
        class1 = UMLClass(obj[0])
        graph.add_class(class1)
        class2 = UMLClass(obj[1])
        graph.add_class(class1)
        graph.add_implementation(class1, class2)

    for entity in uml.keys():
        graph.add_class(UMLClass(entity, attributes={att: get_attribute_type(att) for att in uml[entity]}))

    return graph
