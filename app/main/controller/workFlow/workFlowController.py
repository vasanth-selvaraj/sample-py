from flask import Blueprint, request, jsonify
from app.main.utils.middleware import auth_token_required

workFlowBluePrint = Blueprint('workflow',__name__)

@workFlowBluePrint.route('/get-workflow',methods=['GET'])
@auth_token_required
def getWorkflow():
    return jsonify({'message':'Successfully Fetched'}), 200