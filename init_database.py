#!/usr/bin/env python3
"""
Database Initialization Script
Sets up the database tables and checks connectivity
"""

import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config.database import (
    create_tables, 
    test_connection, 
    get_database_info,
    engine
)

console = Console()

def main():
    """Initialize the database"""
    
    console.print(Panel("[bold blue]🗄️ EKS Advisor Database Setup[/bold blue]", expand=False))
    
    # Show database configuration
    db_info = get_database_info()
    
    info_table = Table(title="Database Configuration")
    info_table.add_column("Setting", style="cyan")
    info_table.add_column("Value", style="green")
    
    info_table.add_row("Database Type", db_info['type'].upper())
    info_table.add_row("Connection URL", db_info['url'])
    if db_info['file']:
        info_table.add_row("Database File", db_info['file'])
    info_table.add_row("Driver", db_info['engine_info']['driver'])
    info_table.add_row("Pool Size", str(db_info['engine_info']['pool_size']))
    
    console.print(info_table)
    
    # Test connection
    console.print("\n🔌 Testing database connection...")
    if test_connection():
        console.print("✅ Database connection successful")
    else:
        console.print("❌ Database connection failed")
        sys.exit(1)
    
    # Create tables
    console.print("\n📋 Creating database tables...")
    try:
        create_tables()
        console.print("✅ Database tables created successfully")
        
        # Show created tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        
        if table_names:
            console.print(f"\n📊 Created tables: {', '.join(table_names)}")
        else:
            console.print("\n⚠️  No tables were created")
            
    except Exception as e:
        console.print(f"❌ Error creating tables: {e}")
        sys.exit(1)
    
    # Database ready
    console.print("\n🎉 Database setup complete!")
    
    if db_info['type'] == 'sqlite':
        console.print(f"💾 SQLite database file: [bold]{db_info['file']}[/bold]")
        console.print("💡 To use PostgreSQL instead, set DATABASE_URL environment variable:")
        console.print("   [code]export DATABASE_URL='postgresql://user:pass@localhost/eks_advisor'[/code]")
    
    console.print("\n🚀 Ready to track analysis history!")

if __name__ == "__main__":
    main()