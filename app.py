import streamlit as st

# ページ設定を最初に実行
st.set_page_config(
    page_title="ステップ式ブログ記事ジェネレーター",
    page_icon="📝",
    layout="wide"
)

# 必要なライブラリをインポート
import openai
import os
from dotenv import load_dotenv
import time
import json
import re

# 追加ライブラリのインポート（エラーハンドリング付き）
try:
    import pandas as pd
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    st.warning("⚠️ pandas/plotlyが見つかりません。基本機能のみ利用可能です。")

# 環境変数の読み込み
load_dotenv()

# APIキーの読み込み
api_key = os.getenv("OPENAI_API_KEY")

# セッション状態の初期化
if 'keyword' not in st.session_state:
    st.session_state.keyword = ""
if 'title_options' not in st.session_state:
    st.session_state.title_options = []
if 'selected_title' not in st.session_state:
    st.session_state.selected_title = ""
if 'selected_keywords' not in st.session_state:
    st.session_state.selected_keywords = []
if 'generated_article' not in st.session_state:
    st.session_state.generated_article = ""
if 'step1_completed' not in st.session_state:
    st.session_state.step1_completed = False
if 'step2_completed' not in st.session_state:
    st.session_state.step2_completed = False
if 'step3_completed' not in st.session_state:
    st.session_state.step3_completed = False

# タイトル
st.title("📝 ステップ式ブログ記事ジェネレーター")
st.markdown("キーワード → タイトル選択 → 記事生成を1画面で完結")

# APIキーチェック
if not api_key:
    st.error("❌ .envファイルにOPENAI_API_KEYを設定してください")
    st.info("""
    .envファイルの作成方法：
    1. アプリと同じフォルダに「.env」ファイルを作成
    2. 中身：OPENAI_API_KEY=your_api_key_here
    """)
    st.stop()

openai.api_key = api_key

# リセット機能
if st.button("🔄 リセット", type="secondary"):
    for key in ['keyword', 'title_options', 'selected_title', 'selected_keywords', 'generated_article', 'step1_completed', 'step2_completed', 'step3_completed']:
        if key in st.session_state:
            if isinstance(st.session_state[key], str):
                st.session_state[key] = ""
            elif isinstance(st.session_state[key], list):
                st.session_state[key] = []
            else:
                st.session_state[key] = False
    st.rerun()

st.markdown("---")

# ===============================
# ステップ1: キーワード入力
# ===============================
st.header("🔍 ステップ1: ブログのキーワードを入力")

col1, col2 = st.columns([2, 1])

with col1:
    keyword_input = st.text_input(
        "メインキーワード",
        value=st.session_state.keyword,
        placeholder="例: プログラミング学習、料理レシピ、読書感想、ダイエット方法",
        help="ブログで書きたいメインテーマのキーワードを入力してください"
    )

with col2:
    st.markdown("#### 📋 入力例")
    example_keywords = ["プログラミング学習", "簡単料理レシピ", "読書感想", "副業体験談"]
    
    for example in example_keywords:
        if st.button(f"📌 {example}", key=f"example_{example}"):
            st.session_state.keyword = example
            st.rerun()

# タイトル生成ボタン
if st.button("➡️ タイトル候補を生成", type="primary", disabled=not keyword_input):
    try:
        with st.spinner("🤖 SEOタイトル候補を生成中..."):
            client = openai.OpenAI(api_key=api_key)
            
            title_prompt = f"""
あなたはSEO専門家です。以下のキーワードに基づいて、SEOに強いブログタイトルを5つ提案してください。

【メインキーワード】
{keyword_input}

【要求事項】
1. SEOに効果的なタイトル（検索されやすい）
2. クリックしたくなる魅力的なタイトル
3. 30文字以内で収める
4. 各タイトルに最適なSEOキーワードも提案

【出力形式】
以下のJSON形式で出力してください：
{{
  "titles": [
    {{
      "title": "タイトル1",
      "seo_keywords": ["キーワード1", "キーワード2", "キーワード3"]
    }},
    {{
      "title": "タイトル2", 
      "seo_keywords": ["キーワード1", "キーワード2", "キーワード3"]
    }}
  ]
}}
"""
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "あなたはSEO専門家です。JSON形式でのみ回答してください。"},
                    {"role": "user", "content": title_prompt}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            response_text = response.choices[0].message.content
            
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1]
            
            title_data = json.loads(response_text.strip())
            
            st.session_state.keyword = keyword_input
            st.session_state.title_options = title_data["titles"]
            st.session_state.step1_completed = True
            
            st.success("✅ タイトル候補を生成しました！")
            st.rerun()
            
    except Exception as e:
        st.error(f"❌ エラーが発生しました: {str(e)}")

# ===============================
# ステップ2: タイトル選択（コンパクト表示）
# ===============================
if st.session_state.step1_completed and st.session_state.title_options:
    st.markdown("---")
    st.header("📋 ステップ2: ブログタイトルを選択")
    st.markdown(f"**選択したキーワード**: `{st.session_state.keyword}`")
    
    selected_option = None
    
    # CSS でコンパクトなスタイルを追加
    st.markdown("""
    <style>
    .compact-title {
        margin: 5px 0 !important;
        padding: 10px !important;
        border: 1px solid #333;
        border-radius: 5px;
        background-color: #1e1e1e;
    }
    .compact-keywords {
        font-size: 0.8em;
        color: #888;
        margin: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    for i, option in enumerate(st.session_state.title_options):
        col1, col2 = st.columns([5, 1])
        
        with col1:
            # コンパクトな表示
            st.markdown(f"""
            <div class="compact-title">
                <strong>📝 {option['title']}</strong><br>
                <span class="compact-keywords">SEOキーワード: {' • '.join([f"`{kw}`" for kw in option['seo_keywords']])}</span>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)  # ボタンの位置調整
            if st.button(f"✅ 選択", key=f"select_{i}", type="primary"):
                selected_option = i
    
    if selected_option is not None:
        st.session_state.selected_title = st.session_state.title_options[selected_option]['title']
        st.session_state.selected_keywords = st.session_state.title_options[selected_option]['seo_keywords']
        st.session_state.step2_completed = True
        
        st.success(f"✅ 「{st.session_state.selected_title}」を選択しました！")
        st.rerun()

# ===============================
# ステップ3: 記事生成（編集可能な選択内容）
# ===============================
if st.session_state.step2_completed:
    st.markdown("---")
    st.header("📝 ステップ3: 記事生成")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📋 選択内容（編集可能）")
        st.info("ステップ2で選択された内容が自動入力されています。必要に応じて修正してください。")
        
        # 編集可能なメインキーワード
        edited_main_keyword = st.text_input(
            "メインキーワード",
            value=st.session_state.keyword,
            help="ステップ1で入力されたキーワードです。修正可能です。"
        )
        
        # 編集可能なタイトル
        edited_title = st.text_input(
            "ブログタイトル",
            value=st.session_state.selected_title,
            help="ステップ2で選択されたタイトルです。修正可能です。"
        )
        
        # 編集可能なSEOキーワード
        seo_keywords_text = ', '.join(st.session_state.selected_keywords)
        edited_seo_keywords = st.text_input(
            "SEOキーワード",
            value=seo_keywords_text,
            help="ステップ2で選択されたSEOキーワードです。カンマ区切りで追加・修正できます。"
        )
        
        # SEOキーワードをリストに変換
        if edited_seo_keywords.strip():
            edited_seo_keywords_list = [kw.strip() for kw in edited_seo_keywords.split(',') if kw.strip()]
        else:
            edited_seo_keywords_list = []
        
        # 現在の設定内容を表示
        st.markdown("### 🔍 現在の設定内容")
        st.success(f"""
        **メインキーワード**: {edited_main_keyword}
        
        **タイトル**: {edited_title}
        
        **SEOキーワード**: {', '.join(edited_seo_keywords_list) if edited_seo_keywords_list else 'なし'}
        """)
        
        # 追加キーワード入力
        st.markdown("### ➕ 追加キーワード（任意）")
        additional_keywords = st.text_area(
            "記事に含めたい追加キーワード",
            placeholder="例：\n初心者向け\n体験談\n失敗談\n解決方法\n\n（1行に1つずつ入力してください）",
            height=100,
            help="記事により具体性を持たせるために、追加で含めたいキーワードがあれば入力してください。"
        )
        
        # 追加キーワードの処理
        if additional_keywords.strip():
            additional_keywords_list = [kw.strip() for kw in additional_keywords.split('\n') if kw.strip()]
            if additional_keywords_list:
                st.markdown("**追加キーワード一覧:**")
                for kw in additional_keywords_list:
                    st.write(f"• `{kw}`")
        else:
            additional_keywords_list = []
    
    with col2:
        st.markdown("### ⚙️ 記事設定")
        
        word_count = st.selectbox(
            "📏 記事の長さ",
            options=[1500, 2500, 3500],
            format_func=lambda x: f"{x}文字程度" + (" (標準)" if x == 2500 else " (短め)" if x == 1500 else " (詳細)")
        )
        
        tone = st.selectbox(
            "🎨 記事のトーン",
            options=["読みやすい", "専門的", "カジュアル"]
        )
        
        # 最終的なキーワード一覧の表示
        st.markdown("### 📝 記事に使用される全キーワード")
        all_keywords = edited_seo_keywords_list + additional_keywords_list
        if all_keywords:
            keywords_text = ", ".join([f"`{kw}`" for kw in all_keywords])
            st.success(f"**合計 {len(all_keywords)}個**: {keywords_text}")
        else:
            st.warning("キーワードが設定されていません")
    
    # 記事生成ボタン（必要な情報がある場合のみ有効）
    can_generate = edited_main_keyword.strip() and edited_title.strip()
    
    if st.button("🚀 記事を生成する", type="primary", disabled=not can_generate):
        if not can_generate:
            st.error("❌ メインキーワードとタイトルは必須です")
        else:
            try:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("🤖 記事構成を考えています...")
                progress_bar.progress(25)
                
                client = openai.OpenAI(api_key=api_key)
                
                # 編集された内容を使用して記事生成
                all_keywords = edited_seo_keywords_list + additional_keywords_list
                
                article_prompt = f"""
あなたは優秀なSEOライターです。以下の条件で高品質なブログ記事を作成してください。

【記事情報】
- タイトル: {edited_title}
- メインキーワード: {edited_main_keyword}
- SEOキーワード: {', '.join(edited_seo_keywords_list) if edited_seo_keywords_list else 'なし'}
- 追加キーワード: {', '.join(additional_keywords_list) if additional_keywords_list else 'なし'}
- 文字数: 約{word_count}文字
- トーン: {tone}

【要求事項】
1. SEOキーワードと追加キーワードを自然に配置
2. 読者にとって有益で実用的な内容
3. 見出し構成を明確に
4. 導入→本文→まとめの構成
5. 専門性と信頼性を重視
6. 設定されたキーワードを記事内容に反映させる

【出力形式】
# {edited_title}

## はじめに
[読者の興味を引く導入文]

## [見出し2-1]
[内容1]

## [見出し2-2] 
[内容2]

## [見出し2-3]
[内容3]

## まとめ
[記事のまとめと読者へのメッセージ]

---
【この記事のキーワード】
- メインキーワード: {edited_main_keyword}
- SEOキーワード: {', '.join(edited_seo_keywords_list) if edited_seo_keywords_list else 'なし'}
{f"- 追加キーワード: {', '.join(additional_keywords_list)}" if additional_keywords_list else ""}
"""
                
                progress_bar.progress(50)
                status_text.text("✍️ 記事を執筆しています...")
                
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "あなたは優秀なSEOライターです。高品質で検索エンジンに評価される記事を作成してください。"},
                        {"role": "user", "content": article_prompt}
                    ],
                    max_tokens=4000,
                    temperature=0.7
                )
                
                progress_bar.progress(75)
                status_text.text("📝 記事を最終調整しています...")
                
                generated_article = response.choices[0].message.content
                st.session_state.generated_article = generated_article
                st.session_state.step3_completed = True
                
                # 編集された内容をセッション状態に反映
                st.session_state.keyword = edited_main_keyword
                st.session_state.selected_title = edited_title
                st.session_state.selected_keywords = edited_seo_keywords_list
                
                progress_bar.progress(100)
                status_text.text("✅ 記事が完成しました！")
                
                time.sleep(1)
                progress_bar.empty()
                status_text.empty()
                
                st.success("🎉 記事の生成が完了しました！")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ エラーが発生しました: {str(e)}")

# ===============================
# 記事表示と評価
# ===============================
if st.session_state.step3_completed and st.session_state.generated_article:
    st.markdown("---")
    st.header("📄 生成された記事")
    
    # 記事をタブで表示
    if PLOTLY_AVAILABLE:
        tab1, tab2, tab3 = st.tabs(["📖 記事プレビュー", "📋 記事テキスト", "📊 SEO評価"])
    else:
        tab1, tab2 = st.tabs(["📖 記事プレビュー", "📋 記事テキスト"])
    
    with tab1:
        st.markdown(st.session_state.generated_article)
    
    with tab2:
        st.text_area(
            "記事テキスト（コピー用）",
            value=st.session_state.generated_article,
            height=500,
            help="この内容をコピーしてブログに貼り付けることができます"
        )
    
    # SEO評価タブ（plotlyが利用可能な場合のみ）
    if PLOTLY_AVAILABLE:
        with tab3:
            # SEO評価の計算
            article_text = st.session_state.generated_article
            article_length = len(article_text)
            
            # キーワード出現回数の計算
            keyword_counts = {}
            total_keyword_count = 0
            
            for keyword in st.session_state.selected_keywords:
                count = article_text.lower().count(keyword.lower())
                keyword_counts[keyword] = count
                total_keyword_count += count
            
            # 見出し数の計算
            h2_count = len(re.findall(r'^## ', article_text, re.MULTILINE))
            h3_count = len(re.findall(r'^### ', article_text, re.MULTILINE))
            
            # タイトル文字数
            title_length = len(st.session_state.selected_title)
            
            # SEOスコアの計算（100点満点）
            def calculate_seo_score():
                score = 0
                
                # 文字数評価（1500-3000文字が理想）30点
                if 1500 <= article_length <= 3000:
                    score += 30
                elif 1000 <= article_length < 1500 or 3000 < article_length <= 4000:
                    score += 20
                else:
                    score += 10
                
                # キーワード密度評価 25点
                keyword_density = (total_keyword_count / article_length) * 100 if article_length > 0 else 0
                if 1 <= keyword_density <= 3:
                    score += 25
                elif 0.5 <= keyword_density < 1 or 3 < keyword_density <= 5:
                    score += 15
                else:
                    score += 5
                
                # 見出し構造評価 20点
                if h2_count >= 3 and h3_count >= 2:
                    score += 20
                elif h2_count >= 2:
                    score += 15
                elif h2_count >= 1:
                    score += 10
                else:
                    score += 5
                
                # タイトル長評価 15点
                if 20 <= title_length <= 32:
                    score += 15
                elif 15 <= title_length < 20 or 32 < title_length <= 40:
                    score += 10
                else:
                    score += 5
                
                # キーワード種類評価 10点
                if len(st.session_state.selected_keywords) >= 3:
                    score += 10
                elif len(st.session_state.selected_keywords) >= 2:
                    score += 7
                else:
                    score += 3
                
                return min(score, 100)
            
            seo_score = calculate_seo_score()
            
            # SEO評価グラフ
            col1, col2 = st.columns(2)
            
            with col1:
                try:
                    # SEO総合スコア（ゲージチャート）
                    fig_score = go.Figure(go.Indicator(
                        mode = "gauge+number+delta",
                        value = seo_score,
                        domain = {'x': [0, 1], 'y': [0, 1]},
                        title = {'text': "SEO総合スコア", 'font': {'size': 20}},
                        delta = {'reference': 80, 'increasing': {'color': "green"}, 'decreasing': {'color': "red"}},
                        gauge = {
                            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                            'bar': {'color': "darkblue"},
                            'bgcolor': "white",
                            'borderwidth': 2,
                            'bordercolor': "gray",
                            'steps': [
                                {'range': [0, 50], 'color': "#ffcccc"},
                                {'range': [50, 80], 'color': "#ffffcc"},
                                {'range': [80, 100], 'color': "#ccffcc"}
                            ],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': 90
                            }
                        }
                    ))
                    fig_score.update_layout(
                        height=350,
                        margin=dict(l=20, r=20, t=40, b=20),
                        font={'color': "darkblue", 'family': "Arial"}
                    )
                    st.plotly_chart(fig_score, use_container_width=True)
                except Exception as e:
                    st.error(f"スコアグラフエラー: {str(e)}")
                    st.metric("SEO総合スコア", f"{seo_score}/100点")
            
            with col2:
                try:
                    # キーワード出現回数（棒グラフ）
                    if keyword_counts:
                        keywords = list(keyword_counts.keys())
                        counts = list(keyword_counts.values())
                        
                        fig_keywords = go.Figure(data=[
                            go.Bar(
                                x=keywords,
                                y=counts,
                                text=counts,
                                textposition='auto',
                                marker=dict(
                                    color=counts,
                                    colorscale='Blues',
                                    line=dict(color='rgba(50,50,50,0.5)', width=1)
                                ),
                                hovertemplate='<b>%{x}</b><br>出現回数: %{y}回<extra></extra>'
                            )
                        ])
                        
                        fig_keywords.update_layout(
                            title={
                                'text': "SEOキーワード出現回数",
                                'x': 0.5,
                                'xanchor': 'center',
                                'font': {'size': 18}
                            },
                            xaxis_title="キーワード",
                            yaxis_title="出現回数",
                            height=350,
                            margin=dict(l=20, r=20, t=60, b=80),
                            font={'family': "Arial"}
                        )
                        
                        fig_keywords.update_xaxes(tickangle=45)
                        st.plotly_chart(fig_keywords, use_container_width=True)
                    else:
                        st.info("キーワードが検出されませんでした")
                except Exception as e:
                    st.error(f"キーワードグラフエラー: {str(e)}")
                    if keyword_counts:
                        st.write("**キーワード出現回数:**")
                        for keyword, count in keyword_counts.items():
                            st.write(f"• `{keyword}`: {count}回")
            
            # 詳細評価指標
            st.markdown("### 📈 詳細評価指標")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📊 文字数", f"{article_length:,}文字", delta="理想: 1500-3000文字")
            
            with col2:
                keyword_density = (total_keyword_count / article_length) * 100 if article_length > 0 else 0
                st.metric("🔍 キーワード密度", f"{keyword_density:.1f}%", delta="理想: 1-3%")
            
            with col3:
                st.metric("📑 見出し数", f"H2: {h2_count}, H3: {h3_count}", delta="理想: H2≥3, H3≥2")
            
            with col4:
                st.metric("📝 タイトル文字数", f"{title_length}文字", delta="理想: 20-32文字")
    
    # 基本的な記事情報（plotlyがない場合も表示）
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 文字数", f"{len(st.session_state.generated_article):,}文字")
    
    with col2:
        st.metric("🔍 キーワード", st.session_state.keyword)
    
    with col3:
        st.metric("🎯 SEOキーワード数", len(st.session_state.selected_keywords))
    
    with col4:
        st.metric("⭐ 設定トーン", tone if 'tone' in locals() else "未設定")

# フッター
st.markdown("---")
st.markdown("""
### 💡 使い方のコツ

**効果的なキーワード選び**: 具体的で検索ボリュームのあるキーワードを選択
**タイトル選択**: SEOキーワードが豊富で魅力的なタイトルを選択  
**記事の品質**: 生成後は必要に応じて体験談や具体例を追加

### ⚠️ 注意事項
生成された記事は参考として使用し、必要に応じて編集してください
""")
