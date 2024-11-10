roles_permissions = {
    "admin": {
        "description": "Admin role with full access to all features, only for fully trusted students.",
        "permissions": {
            "view_admin_panel": True, # Can view the admin panel
            "manage_database": True, # Can manage the database
            "create_events": True, # Can create events
            "generate_reports": True, # Can generate reports
            "edit_attendance": True, # Can edit attendance records
            "review_suspicious_activity": True, # Can review suspicious activity
            "edit_specific_students": True, # Can edit specific student records
            "view_hours": True, # Can view hours
            "confirm_check_in": True, # Can confirm student check-ins
            "view_action_logs": True # Can view action logs
        }
    },
    "executive": {
        "description": "Role for executives with access to all features except for specific editing privileges.",
        "permissions": {
            "view_admin_panel": True,
            "manage_database": False,
            "create_events": True,
            "generate_reports": True,
            "edit_attendance": False,
            "review_suspicious_activity": True,
            "edit_specific_students": False,
            "view_hours": True,
            "confirm_check_in": True,
            "view_action_logs": True
        }
    },
    "advisor": {
        "description": "Role for teachers with permissions to manage attendance reports, events, and review suspicious activity.",
        "permissions": {
            "view_admin_panel": False,
            "manage_database": False,
            "create_events": True,
            "generate_reports": True,
            "edit_attendance": True,
            "review_suspicious_activity": True,
            "edit_specific_students": True,
            "view_hours": True,
            "confirm_check_in": False,
            "view_action_logs": True
        }
    },
    "mentor": {
        "description": "Role for mentors who can confirm student check-ins, and create events.",
        "permissions": {
            "access_all_features": False,
            "view_admin_panel": False,
            "manage_database": False,
            "create_events": True,
            "generate_reports": False,
            "edit_attendance": False,
            "review_suspicious_activity": False,
            "edit_specific_students": False,
            "view_hours": True,
            "confirm_check_in": True,
            "view_action_logs": False
        }
    },
    "leadership": {
        "description": "Role for student leaders who can create events but cannot edit attendance records.",
        "permissions": {
            "view_admin_panel": False,
            "manage_database": False,
            "create_events": True,
            "generate_reports": False,
            "edit_attendance": False,
            "review_suspicious_activity": False,
            "edit_specific_students": False,
            "view_hours": True,
            "confirm_check_in": True,
            "view_action_logs": False
        }
    },
    "member": {
        "description": "Standard role for students with limited permissions focused on attendance check-in and record viewing.",
        "permissions": {
            "access_all_features": False,
            "view_admin_panel": False,
            "manage_database": False,
            "create_events": False,
            "generate_reports": False,
            "edit_attendance": False,
            "review_suspicious_activity": False,
            "edit_specific_students": False,
            "view_hours": True,
            "confirm_check_in": True,
            "view_action_logs": False
        }
    },
    "unverified": {
        "description": "Role for new users who have not yet been verified by an admin.",
        "permissions": {
            "access_all_features": False,
            "view_admin_panel": False,
            "manage_database": False,
            "create_events": False,
            "generate_reports": False,
            "edit_attendance": False,
            "review_suspicious_activity": False,
            "edit_specific_students": False,
            "view_hours": True,
            "confirm_check_in": False,
            "view_action_logs": False
        }
    }
}