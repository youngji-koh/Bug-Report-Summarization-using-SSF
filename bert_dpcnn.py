import numpy as np
import pandas as pd
from tensorflow.keras.utils import plot_model
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, SpatialDropout1D, Conv1D, Flatten, Dense, Activation, Add, MaxPooling1D

import tensorflow.keras

from sklearn.model_selection import train_test_split
from sklearn.metrics.pairwise import cosine_similarity
# from models.data_process import label2vec, vec2label
# from APSEC_SO.proj.models.data_process import label2vec, vec2label, one_hot
from Util import OneHot

import networkx as nx
from sklearn.pipeline import Pipeline

from tensorflow.keras import backend as k

from sklearn.ensemble import RandomForestClassifier

import joblib

from sklearn.model_selection import StratifiedKFold, GridSearchCV, cross_validate, LeaveOneGroupOut

from sklearn.metrics import accuracy_score, classification_report
import matplotlib.pyplot as plt

from tensorflow.keras.layers import Embedding

from bert_serving.client import BertClient

# data = pd.read_csv("data_without_few.csv")
# desc = np.load("..\\data\\vec\\desc_vec_28.npy")
# name = np.load("..\\data\\vec\\name_vec_28.npy")
#
# feature = np.concatenate((name, desc), axis=1)

# data = pd.read_csv("../data/view/data-p.csv")#name+description
# data = pd.read_csv("../data/view/data0612.csv")#name+description
'''
data = pd.read_csv("APSEC_SO/proj/data/view/EMSEData.csv")#EMSEData
#feature = np.load("../data/vec/proc/no-proc.npy")#name+description_vec
feature = np.load("APSEC_SO/proj/data/vec/proc/procEMSESenVec.npy")#procEMSESenVec
feature = feature.reshape((feature.shape[0], 1, feature.shape[1]))
print("data*******************************************************************************************************************************:")
print(data)
print("feature*******************************************************************************************************************************:")
print(feature)
'''
from bert_serving.client import BertClient


# GPU 메모리 부족 문제 해결
gpus = tensorflow.config.experimental.list_physical_devices('GPU')
if gpus:
  try:
    # Currently, memory growth needs to be the same across GPUs
    for gpu in gpus:
      tensorflow.config.experimental.set_memory_growth(gpu, True)
    logical_gpus = tensorflow.config.experimental.list_logical_devices('GPU')
    print(len(gpus), "Physical GPUs,", len(logical_gpus), "Logical GPUs")
  except RuntimeError as e:
    # Memory growth must be set before GPUs have been initialized
    print(e)



def block(pre, num_filters):
    x = Activation(activation='relu')(pre)
    x = Conv1D(filters=num_filters, kernel_size=3, padding='same', strides=1)(x)
    x = Activation(activation='relu')(x)
    x = Conv1D(filters=num_filters, kernel_size=3, padding='same', strides=1)(x)
    x = Add()([x, pre])
    return x


def DPCNNTrainModel(n_filters, feature, data):
    avg_acc = []
    best_acc = 0
    print("n_filters =", n_filters)
    print("size", feature.shape[0], feature.shape[1], feature.shape[2])
    input_layer = Input(shape=(feature.shape[1], feature.shape[2]))

    '''embedding_layer = Embedding(num_words,
                                EMBEDDING_DIM,
                                embeddings_initializer=Constant(embedding_matrix),
                                input_length=MAX_SEQUENCE_LENGTH,
                                trainable=False)'''

    text_embed = SpatialDropout1D(0.2)(input_layer)
    repeat = 3
    size = 1
    region_x = Conv1D(filters=n_filters, kernel_size=3, padding='same', strides=1)(text_embed)
    x = block(region_x, num_filters=n_filters)

    for _ in range(repeat):
        px = MaxPooling1D(pool_size=3, strides=2, padding='same')(x)
        size = int((size + 1) / 2)
        x = block(px, num_filters=n_filters)

    x = MaxPooling1D(pool_size=size)(x)
    sentence_embed = Flatten()(x)

    dense_layer = Dense(n_filters, activation='relu')(sentence_embed)  # 256=n_filters
    # output = Dense(7, activation='softmax')(dense_layer)
    output = Dense(2, activation='softmax')(dense_layer)

    model = Model(input_layer, output)
    model.compile(loss='categorical_crossentropy', metrics=['accuracy'], optimizer='adam')

    # plot_model(model, to_file='./bert_dpcnn.png', show_shapes=True)
    print(
        "NewData*********************************************************************************************************************************")
    print(data)
    train_feature, test_feature, train, test = train_test_split(feature, data, test_size=0.1, random_state=29)
    print(
        "train_feature*******************************************************************************************************************************:")
    print(train_feature)
    print(
        "train*******************************************************************************************************************************:")
    print(train)
    print(
        "test_feature*******************************************************************************************************************************:")
    print(test_feature)

    # train_label = label2vec(train['label'])
    train_label = np.array([OneHot(label, 2) for label in train['Opinion']])
    print("train_label******************************************************************************\n",
          train_label)

    # test_label = label2vec(test['label'])
    # print("Onehot***********************************************************************************\n", [one_hot(label, 2) for label in test['Opinion']])

    test_label = np.array([OneHot(label, 2) for label in test['Opinion']])

    print("model_fit start")
    history = model.fit(train_feature, train_label, batch_size=32, epochs=50, verbose=1,
                        validation_data=(test_feature, test_label))

    model.save("SOModelData/Bert_DPCNN.h5")


    # model.save('bert_dpcnn.h5')
    # plt.plot(history.history['loss'], label='train')
    # plt.plot(history.history['val_loss'], label='test')
    # plt.plot(history.history['val_accuracy'], label='accuracy')
    # plt.legend()
    # plt.show()
    #
    # pred = model.predict(test_feature)
    # pred_label = list(vec2label(pred))
    # acc = accuracy_score(list(test['label']), pred_label)
    # print('模型在测试集上的准确率为: %.4f.' % acc)
    # print('平均准确率: %.4f, 最高准确率:%.4f, 最低准确率: %.4f' % (
    #     sum(history.history['val_accuracy'][30:]) / len(history.history['val_accuracy'][30:]),
    #     max(history.history['val_accuracy']),
    #     min(history.history['val_accuracy'][30:])))
    # print(classification_report(list(test['label']), pred_label))
    # with open("bert_dpcnn.txt", 'a') as f:
    #     f.write("bert + dpcnn + no-preprocess\n")
    #     f.write('模型在测试集上的准确率为: %.4f.\n' % acc)
    #     f.write('平均准确率: %.4f, 最高准确率:%.4f, 最低准确率: %.4f\n' % (
    #         sum(history.history['val_accuracy'][30:]) / len(history.history['val_accuracy'][30:]),
    #         max(history.history['val_accuracy']),
    #         min(history.history['val_accuracy'][30:])))
    #     f.write(classification_report(list(test['label']), pred_label))
    #     f.write('*' * 80 + '\n')

    with open("./res-2.csv", 'a') as file:
        file.write('%.4f,%.4f,%.4f\n' % (
            sum(history.history['val_acc'][30:]) / len(history.history['val_acc'][30:]),
            max(history.history['val_acc']),
            min(history.history['val_acc'][30:])))
    avg_acc.append((n_filters, sum(history.history['val_acc'][30:]) / len(history.history['val_acc'][30:])))

    print("model.layers***********************************************************************\n",
          len(model.layers))
    print(avg_acc)
    SaveVar(train_feature, test_feature, train_label, test_label)
    # return train_feature, test_feature, train_label, test_label


def reOneHot(label):
    imptLabelList = []
    for i in label:
        if i[0] == 1:
            imptLabelList.append(0)
        else:
            imptLabelList.append(1)

    reOneHotLabel = np.array(imptLabelList)
    return reOneHotLabel


def rfc_Train(trainvec, trainlabel):
    rfc_model = RandomForestClassifier(min_samples_split=10, n_estimators=100, max_features="auto")

    reOneHotTrainLabel = reOneHot(trainlabel)

    '''
    parameters = {
        'clf__n_estimators': (10, 50, 100),
        'clf__min_samples_split': (2, 5, 10),
        'clf__max_features': ("auto", "sqrt", "log2", None),
    }
    pipeline1 = Pipeline([('clf', RandomForestClassifier(class_weight='balanced'))])
    clf1 = GridSearchCV(pipeline1, parameters, scoring='f1_weighted')
    grid_result = clf1.fit(trainvec, trainlabel)

    joblib.dump(grid_result.best_estimator_ , "SOModelData/rfc.pth")
    print("Best: %f using %s" % (grid_result.best_score_, grid_result.best_params_))
    '''
    rfc_model.fit(trainvec, reOneHotTrainLabel)
    joblib.dump(rfc_model, "SOModelData/rfc.pth")


def rfc_Test(testvec, testlabel):
    rfc_model = joblib.load("SOModelData/rfc.pth")
    reOneHotTestLabel = reOneHot(testlabel)
    predictLabel = rfc_model.predict(testvec)
    Accuracy = accuracy_score(reOneHotTestLabel, predictLabel)
    print("RFC_Accuracy:\n", Accuracy)
    return Accuracy


'''
def SOPredict(SentenceList):
    if (len(SentenceList) == 1 and SentenceList[0] == ''):
        return 0
    rfc_model = joblib.load("APSEC_SO/proj/models/rfc.pth")
    SenVec = SenToBertVec(SentenceList)
    #SenVec.resize([1,1,768])
    #print("SenVec\n", SenVec)
    Compressed_Feature = DPCNN_Compressed_Vec_Gen(SenVec)
    #print("1*****************************************************************************")
    predictAnswer = rfc_model.predict(Compressed_Feature)
    #print(predictAnswer)
    predictPos = rfc_model.predict_proba(Compressed_Feature)
    #print("2*****************************************************************************")
    #print(predictPos)
    return predictPos[0][0]
'''


def SOPredict(SenVecList, layermodel, rfc_model):
    SenVecList = np.array(SenVecList)
    SenVecList = SenVecList[:, np.newaxis, :]

    Compressed_Feature = DPCNN_Compressed_Vec_Gen(SenVecList, layermodel)

    predictPos = rfc_model.predict_proba(Compressed_Feature)

    return predictPos[:, 0]

# 문장 벡터들 간의 코사인 유사도를 구한 유사도 행렬 생성
# 유사도 행렬의 크기는 (문장 개수 × 문장 개수)
def similarity_matrix(sentence_embedding, embedding_dim):
  sim_mat = np.zeros([len(sentence_embedding), len(sentence_embedding)])


  for i in range(len(sentence_embedding)):
      for j in range(len(sentence_embedding)):
        sim_mat[i][j] = cosine_similarity(sentence_embedding[i].reshape(1, embedding_dim),
                                          sentence_embedding[j].reshape(1, embedding_dim))[0,0]
  return sim_mat


def calculate_score(sim_matrix):
    nx_graph = nx.from_numpy_array(sim_matrix)
    scores = nx.pagerank(nx_graph)

    return scores

def ranked_sentences(scores):
    ranked_scores = sorted(scores)

    text_rank = []
    for i in range(len(scores)):
        text_rank.append(ranked_scores.index(scores[i])+1)

    return text_rank

def TextRank(SenVecList):
    SenVecList = np.array(SenVecList)

    sim_mat = []
    sim_mat = similarity_matrix(SenVecList, len(SenVecList[0]))
    scores = calculate_score(sim_mat)
    scores = list(scores.values())


    # 점수 대신 rank score 사용
    ranked_scores = ranked_sentences(scores)
    #print(ranked_scores)
    #print(scores)
    return scores, ranked_scores

    # 점수 사용 (0.01보다 작음)
    #return scores

def TitleSimilarity(SenVecList, titleVec):

    SenVecList = np.array(SenVecList)
    titleVec = np.array(titleVec)
    embedding_dim = len(titleVec[0])
    #print(titleVec)
    topic_score= np.zeros([len(SenVecList)])

    for i in range(len(SenVecList)):
        topic_score[i] = cosine_similarity(SenVecList[i].reshape(1, embedding_dim),
                                              titleVec[0].reshape(1, embedding_dim))[0,0]

    #print("toic score", len(topic_score))
    return topic_score

def SenToBertVec(SentenceList):
    bc = BertClient(check_length=False)
    # print("SentenceList", SentenceList)
    sentenceVec = bc.encode(SentenceList)
    sentenceVec = sentenceVec.reshape((sentenceVec.shape[0], 1, sentenceVec.shape[1]))
    return sentenceVec


def SaveVar(train_feature, test_feature, train, test):
    joblib.dump(train_feature, "SOModelData/train_feature.pkg")
    joblib.dump(test_feature, "SOModelData/test_feature.pkg")
    joblib.dump(train, "SOModelData/train.pkg")
    joblib.dump(test, "SOModelData/test.pkg")


def LoadVar():
    train_feature = joblib.load("SOModelData/train_feature.pkg")
    test_feature = joblib.load("SOModelData/test_feature.pkg")
    train = joblib.load("SOModelData/train.pkg")
    test = joblib.load("SOModelData/test.pkg")

    return train_feature, test_feature, train, test


def LoadDPCNNRFC():
    model = tensorflow.keras.models.load_model("SavedModels/Bert_DPCNN.h5")  # Load Bert+DPCNN
    #model = tensorflow.keras.models.load_model("SOModelData/Bert_DPCNN.h5")  # Load Bert+DPCNN

    layermodel = Model(inputs=model.input, outputs=model.layers[-2].output)

    try:
        rfc_model = joblib.load("SavedModels/rfc.pth")
        #rfc_model = joblib.load("SOModelData/rfc.pth")
    except:
        print("There is no rfc.pth")
        rfc_model = None

    return layermodel, rfc_model


def DPCNN_Compressed_Vec_Gen(feature, layermodel):
    # print("DPCNN_Compressed_Vec_Gen feature\n", feature)

    compressedFeature = layermodel.predict(feature)

    return compressedFeature


def ModelTrain(filterNum):
    #data = pd.read_csv("SO-ModelTrainData.csv")  # EMSEData
    # feature = np.load("../data/vec/proc/no-proc.npy")#name+description_vec
    #feature = np.load("SOModelData/procEMSESenVec.npy")  # procEMSESenVec
    #feature = feature.reshape((feature.shape[0], 1, feature.shape[1]))

    data = pd.read_csv("EMSEData.csv")  # EMSEData

    data = data.dropna()
    check_nan_in_data = data.isnull().values.any()
    #print(check_nan_in_data)
    datalist = list(np.array(data['Sentence'].tolist()))

    feature = np.load("procEMSESenVec.npy")  # procEMSESenVec

    DPCNNTrainModel(filterNum, feature, data)

    layermodel, _ = LoadDPCNNRFC()

    train_feature, test_feature, train, test = LoadVar()

    RFC_input_train_vec = DPCNN_Compressed_Vec_Gen(train_feature, layermodel)
    RFC_input_test_vec = DPCNN_Compressed_Vec_Gen(test_feature, layermodel)

    rfc_Train(RFC_input_train_vec, train)
    testResult = rfc_Test(RFC_input_test_vec, test)

    return testResult


# ModelTrain(280)

def optimizeParameter():
    filterList = [100, 200, 280, 350, 400]
    bestac = 0
    bestFilterNum = 0
    for i in filterList:
        result = ModelTrain(i)
        print("{} have acc : {}".format(str(i), str(result)))
        if (result > bestac):
            bestac = result
            bestFilterNum = i
    return bestFilterNum, bestac




#if __name__ == "__main__":


    # print("data*******************************************************************************************************************************:")
    # print(data)
    # print("feature*******************************************************************************************************************************:")
    # print(feature)

    #ModelTrain(350)

    # bfNum, bestac = optimizeParameter()
    #
    # print("best filter num", bfNum)
    # print("acc", bestac)


    # feature 생성 (bert client 이용)
    # data = pd.read_csv("EMSEData.csv")  # EMSEData
    #
    # data = data.dropna()
    # check_nan_in_data = data.isnull().values.any()
    # #print(check_nan_in_data)
    # datalist = list(np.array(data['Sentence'].tolist()))
    #
    # np.save("procEMSESenVec",SenToBertVec(datalist))
