# frontend/assets/styles.py

LIGHT_THEME = """
    QWidget {
        background-color: #ffffff;
        color: #333333;
        font-family: 'Segoe UI', Arial, sans-serif;
    }
    
    QLabel {
        color: #2c3e50;
    }
    
    QLineEdit {
        padding: 10px;
        border: 1px solid #dcdde1;
        border-radius: 5px;
        background-color: #f5f6fa;
        font-size: 14px;
    }
    
    QLineEdit:focus {
        border: 2px solid #3498db;
    }
    
    QPushButton {
        background-color: #2c3e50;
        color: white;
        padding: 10px;
        border-radius: 5px;
        font-weight: bold;
        font-size: 14px;
    }
    
    QPushButton:hover {
        background-color: #34495e;
    }
    
    QProgressBar {
        border: 1px solid #dcdde1;
        border-radius: 5px;
        text-align: center;
        background-color: #f5f6fa;
    }
    
    QProgressBar::chunk {
        background-color: #3498db;
        width: 10px;
    }
"""