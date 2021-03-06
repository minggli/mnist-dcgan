#!/usr/bin/env python
"""
app

flask app serving external client calls.
"""
import logging
from random import randint

from flask import Flask
from flask_restplus import Api, Namespace, Resource

from helper import _validate_integer
from serving import grpc_generate
from config import APP_CONFIG

logger = logging.getLogger(__name__)

application = Flask(__name__)
application.config.update(APP_CONFIG)
ns = Namespace('generate', description='Generate images.')
api = Api(
    title='Wasserstein GAN',
    version='1.0',
    description='Generate images using GANs')


@ns.route('/', defaults={'digit': None})
@ns.route('/<int:digit>')
@ns.doc(params={'digit': '0-9 single integer'})
class Generate(Resource):
    def get(self, digit):
        if _validate_integer(digit) is None:
            digit = randint(0, 9)
        logger.info(f"request received to generate {digit}.")
        img = grpc_generate(digit)
        logger.info("image generated successfully.")
        return img


api.add_namespace(ns)
api.init_app(application)

# TODO Wasserstein loss doesn't discriminate real or fake image like original
# GAN loss function, more work needed to reuse Critic/Discriminator
# to classify generated image. Loss function must include supervise element.
# @app.route('/predict', methods=['GET', 'POST'])
# def predict():
#     if request.method == 'POST':
#         if 'file' not in request.files:
#             return redirect(request.url)
#         f = request.files['file']
#         prob = grpc_predict(f)
#         return render_template('predict.html', result=prob)
#     return render_template('predict.html')

if __name__ == '__main__':
    application.run(host='0.0.0.0', port='8000', debug=True)
