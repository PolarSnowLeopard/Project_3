from flask import Flask, request, send_file
from flask_restx import Api, Resource
from flask_cors import CORS
import logging
from core import query_nl2gql, query_and_generate_report
import os
import uuid
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

api = Api(app, version='1.0', 
         title='金融风险报告生成服务',
         description='提供自然语言查询转换和金融风险报告生成服务',
         doc='/docs')

# 创建命名空间
ns = api.namespace('api', description='课题三接口')

# 定义查询参数模型
query_parser = api.parser()
query_parser.add_argument('query',
                         type=str,
                         location='args',
                         required=True,
                         help='查询语句')

def generate_unique_filename() -> str:
    """生成唯一的文件名。

    Returns:
        str: 唯一的文件名，格式为：timestamp_uuid.pdf
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    return f"{timestamp}_{unique_id}.pdf"

def cleanup_file(file_path: str) -> None:
    """清理指定的文件。

    Args:
        file_path: 要清理的文件路径
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.debug(f"已清理文件: {file_path}")
    except Exception as e:
        logger.error(f"清理文件失败: {e}")

@ns.route('/nl2gql')
class NL2GQL(Resource):
    @ns.expect(query_parser)
    @ns.doc(responses={
        200: 'Success',
        400: 'Validation Error',
        500: 'Internal Server Error'
    })
    def get(self):
        """
        将自然语言查询转换为图数据库查询并执行
        
        参数:
        - query: 自然语言查询字符串
        """
        try:
            query = request.args.get('query')
            if not query:
                logger.error("未提供query参数")
                return {'error': '请提供query参数'}, 400
            
            logger.debug(f"开始处理查询: {query}")
            result = query_nl2gql(query)
            
            if result is None:
                return {'error': '查询执行失败'}, 500
                
            return {'result': result}
            
        except Exception as e:
            logger.exception("处理过程出错")
            return {'error': f"处理过程出错: {str(e)}"}, 500

@ns.route('/generate-report')
class GenerateReport(Resource):
    @ns.expect(query_parser)
    @ns.doc(responses={
        200: 'Success',
        400: 'Validation Error',
        500: 'Internal Server Error'
    })
    def get(self):
        """
        生成金融风险报告PDF文档并返回文件
        
        参数:
        - query: 用于生成报告的查询语句
        
        返回:
        - PDF文件: 生成的报告文件
        """
        output_path = None
        try:
            query = request.args.get('query')
            if not query:
                logger.error("未提供query参数")
                return {'error': '请提供query参数'}, 400
            
            logger.debug(f"开始生成报告，查询: {query}")
            
            # 生成唯一的文件名
            filename = generate_unique_filename()
            output_path = os.path.join('output', filename)
            
            # 生成报告
            success = query_and_generate_report(query, output_path)
            if not success:
                return {'error': '报告生成失败'}, 500
            
            # 检查文件是否存在
            if not os.path.exists(output_path):
                return {'error': '报告文件未生成'}, 500
            
            # 使用try-finally确保文件会被清理
            try:
                return send_file(
                    output_path,
                    mimetype='application/pdf',
                    as_attachment=True,
                    download_name='financial_report.pdf'
                )
            finally:
                # 在发送文件后清理
                cleanup_file(output_path)
            
        except Exception as e:
            # 如果过程中出错，也要清理文件
            if output_path:
                cleanup_file(output_path)
            logger.exception("处理过程出错")
            return {'error': f"处理过程出错: {str(e)}"}, 500

@ns.route('/health')
class Health(Resource):
    @ns.doc(responses={200: 'Success'})
    def get(self):
        """
        健康检查接口
        用于检查API服务是否正常运行
        """
        return {'status': 'healthy'}

if __name__ == '__main__':
    # 确保输出目录存在
    os.makedirs('output', exist_ok=True)
    
    # 启动时清理output目录中的所有PDF文件
    for file in os.listdir('output'):
        if file.endswith('.pdf'):
            cleanup_file(os.path.join('output', file))
    
    app.run(host='0.0.0.0', port=5000)
