import os
import sys

def main():
    print("🧾 GST Reconciliation System")
    print("="*40)
    print("1. 🖥️  Launch Desktop GUI")
    print("2. 🌐 Launch Web Dashboard")
    print("3. ❌ Exit")
    print("="*40)
    
    choice = input("Select option (1-3): ")
    
    if choice == '1':
        print("\n🚀 Starting Desktop GUI...")
        os.system("python gst_gui_app.py")
    elif choice == '2':
        print("\n🚀 Starting Web Dashboard...")
        print("Dashboard will open at: http://localhost:8501")
        os.system("streamlit run web_dashboard.py")
    elif choice == '3':
        print("\n👋 Goodbye!")
        sys.exit()
    else:
        print("\n❌ Invalid choice!")
        main()

if __name__ == "__main__":
    main()