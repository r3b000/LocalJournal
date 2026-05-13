"""
Mental Development Page
Track emotional patterns and psychological development
"""

import streamlit as st
import traceback
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from pathlib import Path
from utils.paths import get_database_path, get_issue_tracker_dir
from database.mental_db import (
    log_mental_issue,
    save_worksheet,
    get_issue_summary,
    get_completed_worksheets,
    get_all_issues,
    reset_tracker_without_worksheet,
    delete_mental_issue,
    delete_mental_worksheet
)
from database.trades_db import get_all_trades
from components.account_selector import render_account_selector
from config.constants import (
    MENTAL_CATEGORIES,
    EXECUTION_ISSUES,
    RISK_ISSUES,
    MANAGEMENT_ISSUES,
    EMOTIONS,
    WORKSHEET_TRIGGER_COUNT
)

st.set_page_config(page_title="Mental Development", page_icon="🧠", layout="wide")

def init_worksheet_state():
    """Initialize worksheet-related session state variables"""
    required_keys = {
        'show_worksheet': False,
        'worksheet_category': None,
        'worksheet_trigger_type': None,
        'worksheet_trigger_value': None,
        'worksheet_count': 0,
        'worksheet_blocking': True
    }
    
    for key, default_value in required_keys.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

def clear_worksheet_state():
    """Clear worksheet session state"""
    st.session_state['show_worksheet'] = False
    st.session_state['worksheet_category'] = None
    st.session_state['worksheet_trigger_type'] = None
    st.session_state['worksheet_trigger_value'] = None
    st.session_state['worksheet_count'] = 0

def trigger_worksheet(category: str, trigger_type: str, trigger_value: str, count: int):
    """Trigger worksheet modal with given parameters"""
    st.session_state['show_worksheet'] = True
    st.session_state['worksheet_category'] = category
    st.session_state['worksheet_trigger_type'] = trigger_type
    st.session_state['worksheet_trigger_value'] = trigger_value
    st.session_state['worksheet_count'] = count
    st.session_state['worksheet_blocking'] = True

def export_mental_dev_data_to_csv(db_path, account_id, account_name):
    """Export all mental development data to CSV files in account-specific folder"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        issue_tracker_dir = get_issue_tracker_dir()
        account_export_dir = issue_tracker_dir / "exports" / account_name.replace(" ", "_")
        account_export_dir.mkdir(parents=True, exist_ok=True)
        
        all_issues = get_all_issues(db_path, account_id)
        worksheets = get_completed_worksheets(db_path, account_id)
        
        export_data = []
        
        if all_issues:
            for issue in all_issues:
                export_data.append({
                    'Issue_ID': issue.get('issue_id'),
                    'Account_Name': account_name,
                    'Category': issue.get('issue_category'),
                    'Issue_Type': issue.get('issue_type'),
                    'Emotion': issue.get('emotion'),
                    'Trade_ID': issue.get('trade_id', 'N/A'),
                    'Comments': issue.get('comments'),
                    'Logged_At': issue.get('logged_at')
                })
        
        issues_file_path = None
        if export_data:
            df_issues = pd.DataFrame(export_data)
            issues_file_path = account_export_dir / f"mental_dev_issues_{timestamp}.csv"
            df_issues.to_csv(issues_file_path, index=False)
        
        worksheet_data = []
        if worksheets:
            for ws in worksheets:
                worksheet_data.append({
                    'Worksheet_ID': ws.get('worksheet_id'),
                    'Account_Name': account_name,
                    'Category': ws.get('issue_category'),
                    'Trigger_Type': ws.get('trigger_type'),
                    'Trigger_Value': ws.get('trigger_value'),
                    'Occurrence_Count': ws.get('occurrence_count'),
                    'Emotional_Pattern': ws.get('emotional_pattern'),
                    'Root_Cause': ws.get('root_cause'),
                    'Challenge_Response': ws.get('challenge_response'),
                    'Action_Plan': ws.get('action_plan'),
                    'Expected_Outcome': ws.get('expected_outcome'),
                    'Completed_At': ws.get('completed_at')
                })
        
        worksheets_file_path = None
        if worksheet_data:
            df_worksheets = pd.DataFrame(worksheet_data)
            worksheets_file_path = account_export_dir / f"mental_dev_worksheets_{timestamp}.csv"
            df_worksheets.to_csv(worksheets_file_path, index=False)
        
        return issues_file_path, worksheets_file_path, len(export_data), len(worksheet_data)
    
    except Exception as e:
        st.error(f"[ X ] Error exporting data: {str(e)}")
        return None, None, 0, 0

def render_mental_dev_charts(all_issues):
    """Render visualization charts for mental development patterns"""
    if not all_issues:
        st.info("No data available for visualization. Log some issues to see charts.")
        return
    
    category_counts = {}
    emotion_counts = {}
    issue_type_counts = {}
    
    for issue in all_issues:
        category = issue.get('issue_category', 'Unknown')
        emotion = issue.get('emotion', 'Unknown')
        issue_type = issue.get('issue_type', 'Unknown')
        
        category_counts[category] = category_counts.get(category, 0) + 1
        emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        issue_type_counts[issue_type] = issue_type_counts.get(issue_type, 0) + 1
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Issues by Category',
            'Top 10 Emotions',
            'Top 10 Issue Types',
            'Category Distribution'
        ),
        specs=[[{'type': 'bar'}, {'type': 'bar'}],
               [{'type': 'bar'}, {'type': 'pie'}]]
    )
    
    categories = list(category_counts.keys())
    category_values = list(category_counts.values())
    
    fig.add_trace(
        go.Bar(
            x=categories,
            y=category_values,
            marker_color='#7e3abe',
            name='Categories',
            showlegend=False
        ),
        row=1, col=1
    )
    
    top_emotions = sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    emotions_list = [e[0] for e in top_emotions]
    emotions_values = [e[1] for e in top_emotions]
    
    fig.add_trace(
        go.Bar(
            x=emotions_list,
            y=emotions_values,
            marker_color='#e74c3c',
            name='Emotions',
            showlegend=False
        ),
        row=1, col=2
    )
    
    top_issues = sorted(issue_type_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    issues_list = [i[0] for i in top_issues]
    issues_values = [i[1] for i in top_issues]
    
    fig.add_trace(
        go.Bar(
            x=issues_list,
            y=issues_values,
            marker_color='#3498db',
            name='Issue Types',
            showlegend=False
        ),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Pie(
            labels=categories,
            values=category_values,
            marker=dict(colors=['#7e3abe', '#e74c3c', '#3498db']),
            name='Distribution',
            showlegend=True
        ),
        row=2, col=2
    )
    
    fig.update_xaxes(tickangle=45, row=1, col=2)
    fig.update_xaxes(tickangle=45, row=2, col=1)
    
    fig.update_layout(
        height=800,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        margin=dict(l=40, r=40, t=60, b=40)
    )
    
    st.plotly_chart(fig, use_container_width=True)

###### ICONS

from utils.png_icons import *

# Main execution with error handling
try:
    @st.dialog("[ ! ] RECURRING PATTERN DETECTED - ACTION REQUIRED", width="large")
    def render_worksheet_modal(db_path, account_id):
        """Render the worksheet modal as a blocking dialog"""
        
        try:
            category = st.session_state.get('worksheet_category')
            trigger_type = st.session_state.get('worksheet_trigger_type')
            trigger_value = st.session_state.get('worksheet_trigger_value')
            count = st.session_state.get('worksheet_count', 0)
            
            if not all([category, trigger_type, trigger_value]):
                st.error("[ X ] Invalid worksheet state. Please try logging the issue again.")
                if st.button("Close and Reset"):
                    clear_worksheet_state()
                    st.rerun()
                return
            
            if trigger_type == "EMOTION":
                banner_message = f"**{trigger_value}** emotion has occurred **{count} times** in **{category}**"
                subtitle = f"This emotion is appearing frequently across different issues in {category}"
            elif trigger_type == "ISSUE":
                banner_message = f"**{trigger_value}** issue has occurred **{count} times** in **{category}**"
                subtitle = f"This issue is appearing frequently with different emotions in {category}"
            else:
                banner_message = f"Pattern detected: **{trigger_value}** ({count} times in {category})"
                subtitle = "Complete worksheet to continue tracking"
            
            st.error(banner_message)
            st.warning(
                f"[ ! ] **IMPORTANT:** Complete this worksheet to reset the counter and continue tracking.\n\n"
                f"{subtitle}\n\n"
                f"**You cannot log new issues until this worksheet is completed or dismissed.**"
            )
            st.markdown("---")
            
            with st.form("worksheet_modal_form", clear_on_submit=False, border=False):
                st.subheader("Mental Development Worksheet")
                
                col_info1, col_info2, col_info3, col_info4 = st.columns(4)
                with col_info1:
                    st.markdown("**Category:**")
                    st.caption(category)
                with col_info2:
                    st.markdown("**Trigger Type:**")
                    st.caption(trigger_type)
                with col_info3:
                    st.markdown("**Pattern:**")
                    st.caption(trigger_value)
                with col_info4:
                    st.markdown("**Occurrences:**")
                    st.caption(count)
                
                st.markdown("---")
                
                st.markdown("### A. Identify the Issue")
                emotional_pattern = st.text_area(
                    "What is the pattern you've identified?",
                    placeholder=f"Describe how '{trigger_value}' manifests in your trading...",
                    key="ws_emotional_pattern",
                    height=100
                )
                
                st.markdown("### B. Understanding the Root Cause")
                root_cause = st.text_area(
                    "What is causing this pattern?",
                    placeholder="What triggers this? What's the underlying cause?",
                    key="ws_root_cause",
                    height=100
                )
                
                st.markdown("### C. Challenge Your Issue")
                challenge_response = st.text_area(
                    "How can you challenge this pattern?",
                    placeholder="What evidence contradicts this? Is it rational?",
                    key="ws_challenge_response",
                    height=100
                )
                
                st.markdown("### D. Action Plan for Improvement")
                action_plan = st.text_area(
                    "What specific actions will you take?",
                    placeholder="List concrete steps to address this issue...",
                    key="ws_action_plan",
                    height=100
                )
                
                st.markdown("### E. Expected Outcome and Future Approach")
                expected_outcome = st.text_area(
                    "What do you expect to happen when you implement this plan?",
                    placeholder="How will this change your trading behavior?",
                    key="ws_expected_outcome",
                    height=100
                )
                
                st.markdown("---")
                
                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    submit_worksheet = st.form_submit_button(
                        "Submit Worksheet",
                        type="primary",
                        use_container_width=True
                    )
                
                with col_btn2:
                    reset_and_dismiss = st.form_submit_button(
                        "Reset Counter & Dismiss",
                        use_container_width=True
                    )
                
                if submit_worksheet:
                    if not all([emotional_pattern, root_cause, challenge_response, action_plan, expected_outcome]):
                        st.error("[ X ] Please complete all sections of the worksheet before submitting")
                    else:
                        worksheet_data = {
                            'emotional_pattern': emotional_pattern,
                            'root_cause': root_cause,
                            'challenge_response': challenge_response,
                            'action_plan': action_plan,
                            'expected_outcome': expected_outcome
                        }
                        
                        success = save_worksheet(
                            db_path,
                            account_id,
                            category,
                            trigger_type,
                            trigger_value,
                            count,
                            worksheet_data
                        )
                        
                        if success:
                            st.success(" Worksheet completed and saved successfully!")
                            st.info(f"The counter for '{trigger_value}' in {category} has been reset to 0")
                            clear_worksheet_state()
                            st.rerun()
                        else:
                            st.error("[ X ] Failed to save worksheet. Please try again.")
                
                if reset_and_dismiss:
                    st.warning("[ ! ] You are resetting the counter without completing the worksheet")
                    
                    with st.spinner("Resetting tracker..."):
                        success = reset_tracker_without_worksheet(
                            db_path,
                            account_id,
                            category,
                            trigger_type,
                            trigger_value
                        )
                    
                    if success:
                        st.info(
                            f" Counter for '{trigger_value}' in {category} has been reset to 0.\n\n"
                            f"**Note:** No worksheet was saved. This pattern will trigger again after {WORKSHEET_TRIGGER_COUNT} more occurrences."
                        )
                        clear_worksheet_state()
                        st.rerun()
                    else:
                        st.error("[ X ] Failed to reset tracker. Please try again or contact support.")
        
        except Exception as e:
            st.error(f"[ X ] Error rendering worksheet: {str(e)}")
            st.code(traceback.format_exc())
            if st.button("Close and Reset"):
                clear_worksheet_state()
                st.rerun()
    
    def render_issue_form(db_path, account_id, category, issue_options, form_key, trades):
        """Render issue logging form for a specific category"""
        
        if st.session_state.get('show_worksheet', False):
            st.warning(
                f"[ ! ] **Worksheet pending:** Complete or dismiss the recurring pattern worksheet before logging new issues."
            )
            if st.button(f"Open Pending Worksheet", key=f"{form_key}_open_worksheet"):
                st.rerun()
            return
        
        try:
            trade_options = ["No Trade Selected"] + [
                f"#{t['trade_id']} - {t['symbol']} {t['direction']}" for t in trades
            ]
            
            with st.form(f"{form_key}_form"):
                selected_trade = st.selectbox(
                    "Select Trade (Optional)",
                    options=trade_options,
                    key=f"{form_key}_trade"
                )
                
                issue_type = st.selectbox(
                    f"{category} Issue*",
                    options=issue_options,
                    key=f"{form_key}_issue"
                )
                
                emotion = st.selectbox(
                    "Emotion*",
                    options=EMOTIONS,
                    key=f"{form_key}_emotion"
                )
                
                comments = st.text_area(
                    "Comments*",
                    placeholder="What happened? Why did this occur?",
                    key=f"{form_key}_comments"
                )
                
                submitted = st.form_submit_button(
                    f"Log {category} Issue",
                    type="primary"
                )
                
                if submitted:
                    if not issue_type or not emotion or not comments:
                        st.error("[ X ] Please fill all required fields")
                        return
                    
                    trade_id = None
                    if selected_trade != "No Trade Selected":
                        try:
                            trade_id = int(selected_trade.split("#")[1].split(" ")[0])
                        except (ValueError, IndexError) as e:
                            st.error(f"[ X ] Invalid trade selection: {e}")
                            return
                    
                    issue_id, show_worksheet, trigger_type, trigger_value = log_mental_issue(
                        db_path,
                        account_id,
                        category,
                        issue_type,
                        emotion,
                        comments,
                        trade_id
                    )
                    
                    if issue_id:
                        st.success(f" {category} issue logged successfully!")
                        
                        if show_worksheet and trigger_type and trigger_value:
                            trigger_worksheet(
                                category,
                                trigger_type,
                                trigger_value,
                                WORKSHEET_TRIGGER_COUNT
                            )
                            st.rerun()
                    else:
                        st.error("[ X ] Failed to log issue. Please try again.")
        
        except Exception as e:
            st.error(f"[ X ] Error in issue form: {str(e)}")
            st.code(traceback.format_exc())
    
    init_worksheet_state()
    
    icon_header("icons/mental_dev.png", "Mental Development", level="h3")

    st.markdown("Track your trading psychology and emotional patterns")
    st.markdown("---")
    
    db_path = get_database_path()
    
    if not db_path or not db_path.exists():
        st.error("[ X ] Database not found. Please check your setup.")
        st.stop()
    
    selected_account = render_account_selector()
    
    if not selected_account:
        st.info("Please select or create an account to continue")
        st.stop()
    
    account_id = selected_account.get('account_id')
    
    if not account_id:
        st.error("[ X ] Invalid account selection")
        st.stop()
    
    if st.session_state.get('show_worksheet', False):
        render_worksheet_modal(db_path, account_id)
        st.stop()
    
    st.write(f"**Tracking issues for:** {selected_account.get('account_name', 'Unknown')}")
    st.markdown("---")
    
    issue_summary = get_issue_summary(db_path, account_id)
    
    if not issue_summary:
        issue_summary = {
            'Trade Execution': 0,
            'Risk Management': 0,
            'Trade Management': 0,
            'total': 0
        }
    
    col_sum1, col_sum2, col_sum3, col_sum4 = st.columns(4)
    
    with col_sum1:
        st.metric("Total Issues", issue_summary.get('total', 0))
    
    with col_sum2:
        st.metric("Execution Issues", issue_summary.get('Trade Execution', 0))
    
    with col_sum3:
        st.metric("Risk Issues", issue_summary.get('Risk Management', 0))
    
    with col_sum4:
        st.metric("Management Issues", issue_summary.get('Trade Management', 0))
    
    st.markdown("---")
    
    trades = get_all_trades(db_path, account_id)
    
    if trades is None:
        trades = []
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "Trade Execution",
        "Risk Management",
        "Trade Management",
        "Summary & Analysis"
    ])
    
    with tab1:
        st.subheader("-> Log Trade Execution Issue")
        render_issue_form(
            db_path,
            account_id,
            "Trade Execution",
            EXECUTION_ISSUES,
            "execution",
            trades
        )
    
    with tab2:
        st.subheader("->  Log Risk Management Issue")
        render_issue_form(
            db_path,
            account_id,
            "Risk Management",
            RISK_ISSUES,
            "risk",
            trades
        )
    
    with tab3:
        st.subheader("-> Log Trade Management Issue")
        render_issue_form(
            db_path,
            account_id,
            "Trade Management",
            MANAGEMENT_ISSUES,
            "management",
            trades
        )
    
    with tab4:
        st.subheader(" Export & Visualization")
        
        all_issues = get_all_issues(db_path, account_id)
        worksheets = get_completed_worksheets(db_path, account_id)
        
        col_export1, col_export2 = st.columns(2)
        
        with col_export1:
            if st.button("Export Mental Development Data to CSV", use_container_width=True, type="primary"):
                with st.spinner("Exporting data..."):
                    issues_path, worksheets_path, issues_count, worksheets_count = export_mental_dev_data_to_csv(
                        db_path, 
                        account_id, 
                        selected_account.get('account_name', 'Unknown')
                    )
                    
                    if issues_path or worksheets_path:
                        st.success(" Export completed successfully!")
                        
                        if issues_path:
                            st.info(f"Issues exported: {issues_count} records")
                            st.code(str(issues_path), language=None)
                        else:
                            st.warning("No issues data to export")
                        
                        if worksheets_path:
                            st.info(f"Worksheets exported: {worksheets_count} records")
                            st.code(str(worksheets_path), language=None)
                        else:
                            st.warning("No worksheets data to export")
                    else:
                        st.error("[ X ] No data available to export")
        
        with col_export2:
            total_issues = len(all_issues) if all_issues else 0
            total_worksheets = len(worksheets) if worksheets else 0
            st.metric("Total Issues Logged", total_issues)
            st.metric("Total Worksheets Completed", total_worksheets)
        
        st.markdown("---")
        
        st.subheader(" Mental Development Patterns & Trends")
        
        if all_issues and len(all_issues) > 0:
            render_mental_dev_charts(all_issues)
        else:
            st.info("No data available for visualization. Log some issues to see pattern analysis.")
        
        st.markdown("---")
        
        st.subheader(" Completed Development Worksheets")
        
        if worksheets:
            execution_worksheets = [w for w in worksheets if w.get('issue_category') == 'Trade Execution']
            risk_worksheets = [w for w in worksheets if w.get('issue_category') == 'Risk Management']
            management_worksheets = [w for w in worksheets if w.get('issue_category') == 'Trade Management']
            
            col_ws1, col_ws2, col_ws3 = st.columns(3)
            
            with col_ws1:
                st.metric("Execution Worksheets", len(execution_worksheets))
            
            with col_ws2:
                st.metric("Risk Worksheets", len(risk_worksheets))
            
            with col_ws3:
                st.metric("Management Worksheets", len(management_worksheets))
            
            st.markdown("---")
            
            pattern_counts = {}
            for worksheet in worksheets:
                category = worksheet.get('issue_category', 'Unknown')
                trigger_type = worksheet.get('trigger_type', 'UNKNOWN')
                trigger_value = worksheet.get('trigger_value', 'Unknown')
                
                pattern_key = (category, trigger_type, trigger_value)
                
                if pattern_key not in pattern_counts:
                    pattern_counts[pattern_key] = {
                        'count': 0,
                        'worksheets': []
                    }
                
                pattern_counts[pattern_key]['count'] += 1
                pattern_counts[pattern_key]['worksheets'].append(worksheet)
            
            for pattern_key, pattern_data in pattern_counts.items():
                category, trigger_type, trigger_value = pattern_key
                worksheet_count = pattern_data['count']
                pattern_worksheets = pattern_data['worksheets']
                
                if trigger_type == "EMOTION":
                    pattern_header = f" **{category}** - Emotion: **{trigger_value}** ({worksheet_count} worksheet{'s' if worksheet_count > 1 else ''} completed)"
                elif trigger_type == "ISSUE":
                    pattern_header = f"[ ! ] **{category}** - Issue: **{trigger_value}** ({worksheet_count} worksheet{'s' if worksheet_count > 1 else ''} completed)"
                else:
                    pattern_header = f" **{category}** - {trigger_value} ({worksheet_count} worksheet{'s' if worksheet_count > 1 else ''} completed)"
                
                st.markdown(pattern_header)
                
                for idx, worksheet in enumerate(sorted(pattern_worksheets, key=lambda x: x.get('completed_at', ''), reverse=True), 1):
                    worksheet_id = worksheet.get('worksheet_id')
                    completed_date = str(worksheet.get('completed_at', ''))[:10]
                    completed_time = str(worksheet.get('completed_at', ''))[11:16]
                    
                    expander_title = f"    ├─ Worksheet #{idx} - {completed_date} at {completed_time}"
                    
                    with st.expander(expander_title):
                        col_meta1, col_meta2 = st.columns(2)
                        
                        with col_meta1:
                            st.write(f"**Worksheet ID:** {worksheet_id}")
                            st.write(f"**Category:** {category}")
                            st.write(f"**Trigger Type:** {trigger_type}")
                        
                        with col_meta2:
                            st.write(f"**Pattern:** {trigger_value}")
                            st.write(f"**Occurrences:** {worksheet.get('occurrence_count', 0)}")
                            st.write(f"**Completed:** {worksheet.get('completed_at', 'N/A')}")
                        
                        st.markdown("---")
                        
                        st.markdown("**A. Identified Pattern:**")
                        st.info(worksheet.get('emotional_pattern') or "N/A")
                        
                        st.markdown("**B. Root Cause:**")
                        st.info(worksheet.get('root_cause') or "N/A")
                        
                        st.markdown("**C. Challenge Response:**")
                        st.info(worksheet.get('challenge_response') or "N/A")
                        
                        st.markdown("**D. Action Plan:**")
                        st.info(worksheet.get('action_plan') or "N/A")
                        
                        st.markdown("**E. Expected Outcome:**")
                        st.info(worksheet.get('expected_outcome') or "N/A")
                        
                        st.markdown("---")
                        
                        if st.button("Delete Worksheet", key=f"delete_ws_{worksheet_id}_{idx}", type="secondary"):
                            if f'confirm_delete_ws_{worksheet_id}' not in st.session_state:
                                st.session_state[f'confirm_delete_ws_{worksheet_id}'] = True
                                st.rerun()
                        
                        if st.session_state.get(f'confirm_delete_ws_{worksheet_id}', False):
                            st.warning(f"[ ! ] Confirm deletion of Worksheet #{worksheet_id}? This will also delete the worksheet file.")
                            
                            col_confirm1, col_confirm2 = st.columns(2)
                            
                            with col_confirm1:
                                if st.button("Yes, Delete", key=f"confirm_yes_ws_{worksheet_id}_{idx}", type="primary"):
                                    success = delete_mental_worksheet(db_path, worksheet_id, account_id)
                                    
                                    if success:
                                        st.success(f" Worksheet #{worksheet_id} deleted successfully!")
                                        st.session_state.pop(f'confirm_delete_ws_{worksheet_id}', None)
                                        st.cache_data.clear()
                                        st.rerun()
                                    else:
                                        st.error("[ X ] Failed to delete worksheet. Please try again.")
                            
                            with col_confirm2:
                                if st.button("Cancel", key=f"confirm_no_ws_{worksheet_id}_{idx}"):
                                    st.session_state.pop(f'confirm_delete_ws_{worksheet_id}', None)
                                    st.rerun()
                
                st.markdown("---")
        else:
            st.info(" No worksheets completed yet. Keep tracking your issues!")
        
        st.markdown("---")
        
        st.subheader(" Recent Issues Log")
        
        if all_issues:
            recent_issues = all_issues[:10]
            
            for idx, issue in enumerate(recent_issues):
                issue_id = issue.get('issue_id')
                issue_category = issue.get('issue_category', 'Unknown')
                issue_type = issue.get('issue_type', 'Unknown')
                emotion = issue.get('emotion', 'Unknown')
                logged_at = str(issue.get('logged_at', ''))[:10]
                
                col_issue1, col_issue2 = st.columns([5, 1])
                
                with col_issue1:
                    st.markdown(f"**{issue_category}** - {issue_type} - *{emotion}* | {logged_at}")
                    
                    if issue.get('comments'):
                        st.caption(f" {issue['comments']}")
                
                with col_issue2:
                    if st.button("Delete", key=f"delete_issue_{issue_id}_{idx}", type="secondary"):
                        if f'confirm_delete_{issue_id}' not in st.session_state:
                            st.session_state[f'confirm_delete_{issue_id}'] = True
                            st.rerun()
                
                if st.session_state.get(f'confirm_delete_{issue_id}', False):
                    col_confirm1, col_confirm2 = st.columns([5, 1])
                    
                    with col_confirm1:
                        st.warning(f"[ ! ] Confirm deletion of Issue #{issue_id}?")
                    
                    with col_confirm2:
                        col_yes, col_no = st.columns(2)
                        
                        with col_yes:
                            if st.button("Yes", key=f"confirm_yes_{issue_id}_{idx}", type="primary"):
                                success = delete_mental_issue(db_path, issue_id)
                                
                                if success:
                                    st.success(f" Issue #{issue_id} deleted successfully!")
                                    st.session_state.pop(f'confirm_delete_{issue_id}', None)
                                    st.cache_data.clear()
                                    st.rerun()
                                else:
                                    st.error("[ X ] Failed to delete issue. Please try again.")
                        
                        with col_no:
                            if st.button("No", key=f"confirm_no_{issue_id}_{idx}"):
                                st.session_state.pop(f'confirm_delete_{issue_id}', None)
                                st.rerun()
                
                st.markdown("---")
        else:
            st.info("No issues logged yet.")
    
    st.markdown("---")
    st.caption(
        f"💡 Tip: After {WORKSHEET_TRIGGER_COUNT} occurrences of the same emotion OR issue in a category, "
        "you'll complete a worksheet and the counter resets to track the next pattern."
    )

except Exception as e:
    st.error("[ X ] An error occurred while loading the Mental Development page")
    st.error(f"Error details: {str(e)}")
    
    with st.expander("Show full error trace"):
        st.code(traceback.format_exc())
    
    st.info("Please check the console logs or contact support if this persists")
