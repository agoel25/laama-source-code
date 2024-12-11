import streamlit as st
import json
import request_poller  as rp
import comments_secure as comments
import matplotlib.pyplot as plt

st.title("YouTube Data Processor")
st.markdown("<p style='text-align: center; font-size: 18px;'>Enter a YouTube video URL to analyze its metadata, comments, and trends!</p>", unsafe_allow_html=True)

video_url = st.text_input("Enter YouTube Video URL", placeholder="https://www.youtube.com/watch?v=3IdJGL_gFYw")

if st.button("Submit"):
    if video_url:
        with st.spinner("Processing..."):
            try:
                video_id = comments.extract_video_id(video_url)

                metadata = comments.get_video_metadata(video_id)

                data = comments.get_comments(video_url)
                comment_data = comments.extract_content(data)  

                poller = rp.RequestPoller(video_url, comment_data)
                request_id = poller.req_id
                final = poller.poll()

                if final:
                    result = json.loads(final)  


                    st.divider()

                    card_html = f"""<div style="display: flex; flex-direction: column; justify-content: center; align-items: center; gap: 20px;"><div style="background-color: #f9f9f9; border-radius: 10px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); width: 100%; max-width: 800px; padding: 20px; font-size: 16px; text-align: left;"><h2>{metadata.get('title', 'N/A')}</h2><h3>by {metadata.get('channel_title', 'N/A')}</h3></div><div style="display: flex; justify-content: center; gap: 20px;"><div style="background-color: #f9f9f9; border-radius: 10px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); padding: 10px; font-size: 20px; text-align: center; width: 150px;"><strong>Views:</strong><br>{metadata.get('view_count', 'N/A')}</div><div style="background-color: #f9f9f9; border-radius: 10px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); padding: 10px; font-size: 20px; text-align: center; width: 150px;"><strong>Likes:</strong><br>{metadata.get('like_count', 'N/A')}</div><div style="background-color: #f9f9f9; border-radius: 10px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); padding: 10px; font-size: 20px; text-align: center; width: 150px;"><strong>Comments:</strong><br>{metadata.get('comment_count', 'N/A')}</div></div></div>"""

                    st.markdown(card_html, unsafe_allow_html=True)

                    st.divider()

                    tab1, tab2, tab3 = st.tabs(["📈 Sentiment Analysis", "🗃 Video Suggestions", "Comment Analysis"])

                    # st.markdown(
                    #     f"""
                    #     <div style='font-size:16px; text-align:justify;'>
                    #         <strong>Title:</strong> {metadata.get("title", "N/A")}<br>
                    #         <strong>Channel:</strong> {metadata.get("channel_title", "N/A")}<br>
                    #         <strong>Views:</strong> {metadata.get("view_count", "N/A")}<br>
                    #         <strong>Likes:</strong> {metadata.get("like_count", "N/A")}<br>
                    #         <strong>Comments:</strong> {metadata.get("comment_count", "N/A")}<br>
                    #     </div>
                    #     """,
                    #     unsafe_allow_html=True
                    # )


                    with tab1: 
                        # Display Sentiment Results
                        st.subheader("Sentiment Analysis")

                        st.markdown(
                            f"""
                            <div style='font-size:24px; font-weight:bold; text-align:center; color:#FF4B4B;'>
                            Sentiment Sore: {result.get("sentiment_score_percentage")}
					    	</div>
                            """,
                            unsafe_allow_html=True
                        )
                        st.info(result.get("sentiment_feedback", "No feedback available"))

                        st.divider()

                    with tab2:
                        # Display Video Suggestions
                        st.subheader("Video Suggestions")
                        suggestions = result.get("video_suggestions", "").split("\n")
                        # print(suggestions)
                        # for suggestion in suggestions:
                        #     st.button(
                        #         suggestion,  # Display the entire link
                        #         key=suggestion,
                        #         on_click=lambda s=suggestion: st.write(f"[Open Link]({s})"),
                        #     )

                        suggestions = [s.strip("- ").strip() for s in suggestions]

                        # for suggestion in suggestions:
                        #         # Use st.markd wn to make the suggestion a clickable link
                        #             st.markdown(f"[{suggestion}]({suggestion})", unsafe_allow_html=True)

                        for suggestion in suggestions:
                                st.markdown(f"""<a href="{suggestion}" target="_blank"><button style="display: block; margin: 5px; padding: 10px; color: white; border: none; border-radius: 5px; cursor: pointer;">{suggestion}</button></a>""", unsafe_allow_html=True,)

                        st.divider()

                    with tab3:

                        st.subheader("Top Comments and Trends")
                        top_liked, top_replied = comments.get_top_comments(data, count=10)
                        trends = comments.get_comment_trends_monthly(data)

                        st.markdown("### **Most Liked Comments:**")
                        for idx, comment in enumerate(top_liked, start=1):
                            st.markdown(
                                f"**{idx}. {comment.get('author', 'Anonymous')}:** {comment.get('text', 'No text')} "
                                f"(Likes: {comment.get('likes', 0)})"
                            )

                        st.markdown("### **Most Replied Comments:**")
                        for idx, comment in enumerate(top_replied, start=1):
                            st.markdown(
                                f"**{idx}. {comment.get('author', 'Anonymous')}:** {comment.get('text', 'No text')} "
                                f"(Replies: {comment.get('reply_count', 0)})"
                            )

                        st.markdown("### **Monthly Comment Trends**")
                        if trends:
                            dates, counts = zip(*sorted(trends.items()))
                            plt.figure(figsize=(10, 5))
                            plt.plot(dates, counts, marker="o", color="#FF4B4B", linestyle="--")
                            plt.title("Number of Comments Over Months", fontsize=16)
                            plt.xlabel("Month", fontsize=14)
                            plt.ylabel("Number of Comments", fontsize=14)
                            plt.xticks(rotation=45)
                            st.pyplot(plt)
                        else:
                            st.info("No comment trends available.")
                else:
                    st.error("No data was returned. Please try again.")
            except json.JSONDecodeError:
                st.error("Error processing the results. Please try again.")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
    else:
        st.error("Please enter a valid YouTube URL!")
