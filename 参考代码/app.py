from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import datetime
import csv
import json
from functions import  generate_doc_description, do_review,get_json_content,generate_Persona

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB限制

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': '未选择文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '空文件名'}), 400

    if not file.filename.endswith('.csv'):
        return jsonify({'error': '仅支持CSV文件'}), 400
        
    # 检查CSV行数不超过100条
    # 创建临时文件副本进行行数检查
    temp_content = file.read()
    try:
        decoded_content = temp_content.decode('utf-8')
    except UnicodeDecodeError:
        try:
            decoded_content = temp_content.decode('gbk')
        except UnicodeDecodeError:
            return jsonify({'error': '文件编码不支持，请使用UTF-8或GBK编码的CSV文件'}), 400
            
    line_count = sum(1 for _ in csv.reader(decoded_content.splitlines()))
    if line_count > 300:
        return jsonify({'error': 'CSV文件数据不能超过30条'}), 200

    # 保存原始文件
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.seek(0)  # 重置文件指针以便保存
    file.save(input_path)

    # 处理CSV文件
    output_filename = f'processed_{file.filename}'
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
     
    with open(input_path, 'r', newline='', encoding='utf-8') as infile, \
         open(output_path, 'w', newline='', encoding='utf-8') as outfile:
        
        reader = csv.reader(infile)
        writer = csv.writer(outfile)
        
        # 处理表头
        headers = next(reader)
        try:
            target_column = next(i for col in ['typography_body-l__v5JLj', 'cr-original-review-content (2)', 'review_content'] for i, h in enumerate(headers) if h == col)
            print("目标列索引:", target_column)
        except ValueError:
            target_column = 10  # 第11列（索引从0开始）
        headers.append('用户需求与痛点-使用场景')  
        headers.append('用户需求与痛点-购买动机')
        headers.append('用户需求与痛点-未被满足的需求')
        headers.append('用户需求与痛点-痛点问题')
        headers.append('产品反馈-产品优点')  
        headers.append('产品反馈-产品缺点')  
        headers.append('产品反馈-用户期望建议')  
        headers.append('产品反馈-设计与外观')  
        headers.append('服务评价-物流配送')  
        headers.append('服务评价-售后服务') 
        headers.append('服务评价-售前服务') 
        headers.append('品牌形象与口碑-推荐意愿原因分析') 
        headers.append('品牌形象与口碑-是否愿意推荐给他人') 
        headers.append('品牌形象与口碑-品牌印象') 
        headers.append('感官感受') 
        headers.append('价格感知')  
        writer.writerow(headers)
        
        # 处理数据行
        whole_content = ""
        count = 0
        for row in reader:
            if count >= 100:
                break
            content = row[target_column] 
            print("原始内容：", content)  # 打印原始内容
            whole_content += content + "\n"  # 拼接内容 
            count += 1
        print("完整内容：", whole_content)  # 打印拼接结果
        deal_whole_content = generate_doc_description(whole_content)
        print("处理内容meta：", deal_whole_content)
        persona = generate_Persona(whole_content)
        md_filename = output_filename + f"_persona_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        persona_path = os.path.join('uploads', md_filename)
        os.makedirs('uploads', exist_ok=True)
        with open(persona_path, 'w', encoding='utf-8') as f:
            f.write(persona)
        
        # persona是markdown,转为html
        import markdown
        persona_html = markdown.markdown(persona)

        # 重新打开文件读取数据
        infile.close()
        infile = open(input_path, 'r', newline='', encoding='utf-8')
        reader = csv.reader(infile)
        next(reader)  # 跳过表头
        for row in reader: 
            do_content = row[target_column] 
            # 如果do_content为空或不是字符串，则跳过
            if not isinstance(do_content, str) or not do_content.strip():
                print(f"跳过空或非字符串内容: {do_content}")
                continue
            do_things = do_review(do_content, deal_whole_content)
            print("处理do_things：", do_things)
            # 解析JSON数据
            try:
                do_things_dict = json.loads(get_json_content(do_things))
            except json.JSONDecodeError as e:
                print(f"JSON解析错误: {e}，内容：{do_things}")
                continue
            # 如果do_things_dict不是字典，则跳过
            if not isinstance(do_things_dict, dict):
                print(f"返回内容不是字典: {do_things_dict}")
                continue
            # 按表头顺序提取字段值（列表转字符串，逗号分隔）
            row.append(','.join(do_things_dict.get('人群与场景', {}).get('用户需求与痛点-使用场景', [])))
            row.append(','.join(do_things_dict.get('人群与场景', {}).get('用户需求与痛点-购买动机', [])))
            row.append(','.join(do_things_dict.get('人群与场景', {}).get('用户需求与痛点-未被满足的需求', [])))
            row.append(','.join(do_things_dict.get('人群与场景', {}).get('用户需求与痛点-痛点问题', [])))
            row.append(','.join(do_things_dict.get('功能价值', {}).get('产品反馈-产品优点', [])))
            row.append(','.join(do_things_dict.get('功能价值', {}).get('产品反馈-产品缺点', [])))
            row.append(','.join(do_things_dict.get('功能价值', {}).get('产品反馈-用户期望建议', [])))
            row.append(','.join(do_things_dict.get('功能价值', {}).get('产品反馈-设计与外观', [])))
            row.append(','.join(do_things_dict.get('保障价值', {}).get('服务评价-物流配送', [])))
            row.append(','.join(do_things_dict.get('保障价值', {}).get('服务评价-售后服务', [])))
            row.append(','.join(do_things_dict.get('保障价值', {}).get('服务评价-售前服务', [])))
            row.append(','.join(do_things_dict.get('体验价值', {}).get('品牌形象与口碑-推荐意愿原因分析', [])))
            row.append(','.join(do_things_dict.get('体验价值', {}).get('品牌形象与口碑-是否愿意推荐给他人', [])))
            row.append(','.join(do_things_dict.get('体验价值', {}).get('品牌形象与口碑-品牌印象', [])))
            row.append(','.join(do_things_dict.get('体验价值', {}).get('感官感受', [])))
            row.append(','.join(do_things_dict.get('体验价值', {}).get('价格感知', [])))
            writer.writerow(row) 

    # 词频分析
    word_frequency = {}
    with open(output_path, 'r', newline='', encoding='utf-8') as csvfile:
        for column in ['用户需求与痛点-使用场景', '用户需求与痛点-购买动机','用户需求与痛点-未被满足的需求','用户需求与痛点-痛点问题', '产品反馈-产品优点', 
                     '产品反馈-产品缺点', '产品反馈-用户期望建议', '产品反馈-设计与外观',
                     '服务评价-物流配送', '服务评价-售后服务', '服务评价-售前服务',
                     '品牌形象与口碑-推荐意愿原因分析', '品牌形象与口碑-是否愿意推荐给他人',
                     '品牌形象与口碑-品牌印象', '感官感受', '价格感知']:
            word_frequency[column] = {}
            csvfile.seek(0)  # 重置文件指针到开头
            reader = csv.DictReader(csvfile)
            for row in reader:
                cell_value = row.get(column, '') or ''  # 双重空值保护
                words = cell_value.split(',') if cell_value else []
                for word in words:
                    word = word.strip()
                    if word:
                        word_frequency[column][word] = word_frequency[column].get(word, 0) + 1
            
            # 按词频从大到小排序
            word_frequency[column] = dict(
                sorted(
                    word_frequency[column].items(), 
                    key=lambda item: item[1], 
                    reverse=True
                )
            )
            csvfile.seek(0)  # 重置指针
    
    return jsonify({
        'filename': output_filename,
        'filepath': f'/download/{output_filename}',
        'wordFrequency': word_frequency,
        'persona': persona_html
    })

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)