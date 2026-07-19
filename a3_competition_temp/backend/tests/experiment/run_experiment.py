import json
import csv

def load_questions():
    with open('questions.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def load_scores():
    scores = []
    with open('scores.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            scores.append({
                'question_id': row['question_id'],
                'group': row['group'],
                'factual_score': int(row['factual_score']),
                'citation_score': int(row['citation_score']),
                'personalization_score': int(row['personalization_score'])
            })
    return scores

def calculate_results(scores):
    groups = ['A', 'B', 'C', 'D']
    results = {}
    
    for group in groups:
        group_scores = [s for s in scores if s['group'] == group]
        total_factual = sum(s['factual_score'] for s in group_scores)
        total_citation = sum(s['citation_score'] for s in group_scores)
        total_personalization = sum(s['personalization_score'] for s in group_scores)
        
        results[group] = {
            'factual_accuracy': round(total_factual / 100 * 100),
            'citation_accuracy': round(total_citation / 100 * 100),
            'personalization_match': round(total_personalization / 100 * 100)
        }
    
    return results

def main():
    questions = load_questions()
    scores = load_scores()
    
    print(f"已加载 {len(questions)} 道题目")
    print(f"已加载 {len(scores)} 条评分记录")
    
    results = calculate_results(scores)
    
    print("=" * 60)
    print("A/B/C/D四组对照实验结果")
    print("=" * 60)
    print(f"{'组别':<16} {'事实正确率':<16} {'引用正确率':<16} {'个性化匹配度':<16}")
    print("-" * 60)
    
    for group in ['A', 'B', 'C', 'D']:
        r = results[group]
        print(f"{group:<16} {r['factual_accuracy']:<16} {r['citation_accuracy']:<16} {r['personalization_match']:<16}")
    
    print("-" * 60)
    print("\n实验说明：")
    print("- 测试集：20道计算机网络题目，每题满分5分，总分100分")
    print("- 评分方式：盲评，隐藏组别，随机顺序")
    print("- 评分人：两名非核心开发成员独立评分")
    print("- 模型：讯飞星火大模型（v3.0）")
    print("=" * 60)
    
    with open('summary.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()