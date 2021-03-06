#! /usr/bin/env python
"""
train

deploy computation graph, approximate P(x) through adverserial learning and
export saved_model for serving two signatures.
"""
import os
import tensorflow as tf

from tensorflow.saved_model.builder import SavedModelBuilder
from tensorflow.saved_model.signature_def_utils import (
    predict_signature_def, build_signature_def)
from tensorflow.saved_model.signature_constants import CLASSIFY_METHOD_NAME
from tensorflow.saved_model.tag_constants import SERVING
from tensorflow.saved_model.utils import build_tensor_info

from .graph import Graph, train
from .pipeline import mnist_batch_iter
from config import ServingConfig, NNConfig, d_params, g_params

export_path = os.path.join(ServingConfig.MODEL_BASE_PATH,
                           ServingConfig.MODEL_NAME,
                           ServingConfig.MODEL_VER)

d_train_step, d_loss, g_train_step, g_loss, g_z, g_o, gz, dx, d_real_x, \
    image, p_given_y = Graph(NNConfig, d_params, g_params).build()

y_dx = tf.get_default_graph().get_tensor_by_name('y_{0}:0'.format(dx.name))
y_gz = tf.get_default_graph().get_tensor_by_name('y_{0}:0'.format(gz.name))

config = tf.ConfigProto(allow_soft_placement=True)
config.gpu_options.allow_growth = True
sess = tf.Session(config=config)
sess.run(tf.global_variables_initializer())

train_ops = [sess, mnist_batch_iter, d_real_x, g_z, y_dx, y_gz, d_train_step,
             d_loss, g_train_step, g_loss]

train(*train_ops, config=NNConfig)

generative_signature = predict_signature_def(
        inputs={'noise': g_z, 'y_dx': y_dx, 'y_gz': y_gz},
        outputs={'image': image}
)

# predictive_signature for predict_proba on binary real / fake
tensor_info_d_real_x = build_tensor_info(d_real_x)
tensor_info_y_dx = build_tensor_info(y_dx)
tensor_info_y_gz = build_tensor_info(y_gz)
tensor_info_p_given_y = build_tensor_info(p_given_y)
predictive_signature = build_signature_def(
        inputs={'d_real_x': tensor_info_d_real_x,
                'y_dx': tensor_info_y_dx,
                'y_gz': tensor_info_y_gz},
        outputs={'score': tensor_info_p_given_y},
        method_name=CLASSIFY_METHOD_NAME
)

builder = SavedModelBuilder(export_path)
builder.add_meta_graph_and_variables(
    sess, [SERVING],
    signature_def_map={'generate': generative_signature,
                       'classify': predictive_signature},
    strip_default_attrs=True)

builder.save()
