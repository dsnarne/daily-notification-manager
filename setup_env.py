#!/usr/bin/env python3
"""
Environment Setup Script for DaiLY Notification Manager
This script helps you create and configure your .env file
"""

import os
import shutil
import secrets
import string

def generate_secret_key(length=32):
    """Generate a secure random secret key"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def setup_environment():
    """Set up the environment configuration"""
    print("🚀 DaiLY Notification Manager - Environment Setup")
    print("=" * 60)
    
    # Check if .env already exists
    if os.path.exists('.env'):
        print("⚠️  .env file already exists!")
        response = input("Do you want to overwrite it? (y/N): ").lower()
        if response != 'y':
            print("Setup cancelled. Your existing .env file is preserved.")
            return
    
    # Check if template exists
    if not os.path.exists('env_template.txt'):
        print("❌ env_template.txt not found!")
        print("Please make sure the template file exists in the current directory.")
        return
    
    try:
        # Copy template to .env
        shutil.copy('env_template.txt', '.env')
        print("✅ Created .env file from template")
        
        # Generate a secure secret key
        secret_key = generate_secret_key(50)
        
        # Update the .env file with the generated secret key
        with open('.env', 'r') as f:
            content = f.read()
        
        # Replace the placeholder secret key
        content = content.replace(
            'SECRET_KEY=your-super-secret-key-here-change-this-in-production',
            f'SECRET_KEY={secret_key}'
        )
        
        with open('.env', 'w') as f:
            f.write(content)
        
        print("🔑 Generated and set a secure SECRET_KEY")
        
        print("\n📝 Next Steps:")
        print("1. Edit the .env file with your actual API keys and configuration")
        print("2. Key sections to configure:")
        print("   - Email integration (Gmail, Outlook, SMTP)")
        print("   - Slack integration")
        print("   - Microsoft Teams integration")
        print("   - Webhook settings")
        print("   - Database configuration")
        
        print("\n🔒 Security Notes:")
        print("- Never commit .env to version control")
        print("- Keep your API keys secure")
        print("- Use strong, unique passwords")
        print("- Regularly rotate your keys")
        
        print(f"\n✅ Setup complete! Your .env file is ready at: {os.path.abspath('.env')}")
        
    except Exception as e:
        print(f"❌ Error during setup: {e}")
        print("Please check your file permissions and try again.")

def show_help():
    """Show help information"""
    print("DaiLY Notification Manager - Environment Setup Help")
    print("=" * 50)
    print("\nThis script helps you:")
    print("1. Create a .env file from the template")
    print("2. Generate a secure SECRET_KEY")
    print("3. Set up proper environment configuration")
    
    print("\nUsage:")
    print("  python setup_env.py          # Run the setup")
    print("  python setup_env.py --help   # Show this help")
    
    print("\nRequired files:")
    print("  - env_template.txt (template file)")
    print("  - .gitignore (to exclude .env from version control)")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help']:
        show_help()
    else:
        setup_environment() 