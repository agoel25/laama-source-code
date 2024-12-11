# **LAAMA: YouTube Comment Sentiment Analysis**

Welcome to the source code repository for **LAAMA**, a cloud-based platform for YouTube comment sentiment analysis. This application processes YouTube video data, analyzes audience sentiment, and provides actionable feedback for content creators. Below are instructions to set up and start the application.

---

## **Folder Structure**

- **`backend/`**  
  Contains the code for the two AWS Lambda functions:
  1. **Data Processing Lambda**: Located in the `processing` folder
  2. **Analysis Lambda**: Located in the `analysis` folder

- **`frontend/`**  
  Contains all the code for the frontend, hosted on our EC2 instance:
  - **`app4_secure.py`**: The main Streamlit application file.
  - Additional supporting scripts for UI and API interactions.

---

## **How to Start the Application**

The easiest way to access the application is via this link: http://35.183.216.237/ (**Note:** Please only use the application in light mode as the UI components do not render properly in dark model yet.)

If this doesn't work, please go through the steps below to start the application.

1. **Connect to the EC2 Instance**  
   - Log in to the AWS Management Console.
   - Navigate to the **WebserverVPC** instance in EC2 dashboard.
   - Connect to the instance using EC2 Instance Connect with username set to `ec2-user`.

2. **Navigate to the Application Directory**  
   Once connected, navigate to the directory where the application code resides:
   ```bash
   cd prod/AWS_youtube
   ```
3. **Start the Applciation**
   Start the Streamlit app by running the following command:
   ```bash
   streamlit run app4_secure.py
   ```
4. **Access the Application**
   Open your web browser and navigate to the public IP of the EC2 instance on port 80 or 443 (our secure port): `http://<EC2-Public-IP>:8501`

---

## **Troubleshooting**
If you encounter any issues or have questions, please reach out to us, we will more than happy to help you setup the application in case of unexpected failures.
