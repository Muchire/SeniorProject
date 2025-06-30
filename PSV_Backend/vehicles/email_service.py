# vehicles/email_service.py
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class SaccoEmailService:
    """Service class for handling sacco-related email notifications"""
    
    @staticmethod
    def send_join_request_confirmation(join_request):
        """Send confirmation email to vehicle owner when they submit a join request"""
        try:
            subject = f"PSV Finder - Join Request Submitted to {join_request.sacco.name}"
            
            # Create HTML email content
            html_content = f"""
            <!DOCTYPE html>git fetch origin
git status
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #4CAF50; color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .info-box {{ background: white; padding: 20px; border-left: 4px solid #4CAF50; margin: 20px 0; }}
                    .highlight {{ color: #4CAF50; font-weight: bold; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🚌 PSV Finder</h1>
                        <h2>Join Request Received</h2>
                    </div>
                    <div class="content">
                        <p>Dear <strong>{join_request.owner.get_full_name() or join_request.owner.username}</strong>,</p>
                        
                        <p>Thank you for submitting your join request to <span class="highlight">{join_request.sacco.name}</span>. We have successfully received your application and all required documents.</p>
                        
                        <div class="info-box">
                            <h3>Request Details:</h3>
                            <p><strong>Request ID:</strong> #{join_request.id}</p>
                            <p><strong>Vehicle Registration:</strong> {join_request.vehicle.registration_number}</p>
                            <p><strong>Sacco:</strong> {join_request.sacco.name}</p>
                            <p><strong>Submission Date:</strong> {join_request.requested_at.strftime('%B %d, %Y at %I:%M %p')}</p>
                            <p><strong>Status:</strong> Under Review</p>
                        </div>
                        
                        <h3>What happens next?</h3>
                        <p>• Your application is now under review by {join_request.sacco.name} administrators</p>
                        <p>• You will receive an email notification once your request is processed</p>
                        <p>• The review process typically takes 2-5 business days</p>
                        
                        <div class="info-box">
                            <h3>Sacco Contact Information:</h3>
                            <p><strong>Phone:</strong> {join_request.sacco.contact_number or 'Not provided'}</p>
                            <p><strong>Email:</strong> {join_request.sacco.email or 'Not provided'}</p>
                        </div>
                        
                        <p>If you have any questions, please contact the sacco directly using the information above.</p>
                        
                        <p>Best regards,<br>
                        The PSV Finder Team</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Plain text version
            plain_message = f"""
            PSV Finder - Join Request Confirmation
            
            Dear {join_request.owner.get_full_name() or join_request.owner.username},
            
            Thank you for submitting your join request to {join_request.sacco.name}. 
            
            Request Details:
            - Request ID: #{join_request.id}
            - Vehicle: {join_request.vehicle.registration_number}
            - Sacco: {join_request.sacco.name}
            - Date: {join_request.requested_at.strftime('%B %d, %Y at %I:%M %p')}
            
            Your application is now under review. You will receive an email notification once processed.
            
            Sacco Contact: {join_request.sacco.contact_number or 'Not provided'}
            
            Best regards,
            The PSV Finder Team
            """
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[join_request.owner.email],
                html_message=html_content,
                fail_silently=False,
            )
            
            logger.info(f"Join request confirmation email sent to {join_request.owner.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send join request confirmation email: {str(e)}")
            return False
    
    @staticmethod
    def send_approval_notification(join_request):
        """Send approval notification to vehicle owner"""
        try:
            subject = f"🎉 PSV Finder - Your Join Request has been Approved!"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #4CAF50; color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .success-box {{ background: #d4edda; border: 1px solid #c3e6cb; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                    .location-box {{ background: white; padding: 20px; border-left: 4px solid #4CAF50; margin: 20px 0; }}
                    .highlight {{ color: #4CAF50; font-weight: bold; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🚌 PSV Finder</h1>
                        <h2>Congratulations! Request Approved</h2>
                    </div>
                    <div class="content">
                        <div class="success-box">
                            <h2>✅ Your join request has been approved!</h2>
                        </div>
                        
                        <p>Dear <strong>{join_request.owner.get_full_name() or join_request.owner.username}</strong>,</p>
                        
                        <p>Great news! Your application to join <span class="highlight">{join_request.sacco.name}</span> has been approved.</p>
                        
                        <p><strong>Vehicle Registration:</strong> {join_request.vehicle.registration_number}</p>
                        <p><strong>Approval Date:</strong> {join_request.processed_at.strftime('%B %d, %Y at %I:%M %p')}</p>
                        
                        <div class="location-box">
                            <h3>📍 Next Steps - Visit Sacco Office:</h3>
                            <p><strong>Sacco Name:</strong> {join_request.sacco.name}</p>
                            <p><strong>Location:</strong> {join_request.sacco.location or 'Contact sacco for location details'}</p>
                            <p><strong>Phone:</strong> {join_request.sacco.contact_number}</p>
                            <p><strong>Email:</strong> {join_request.sacco.email or 'Not provided'}</p>
                        </div>
                        
                        <h3>What to bring:</h3>
                        <ul>
                            <li>Original vehicle documents</li>
                            <li>Copy of your ID/Passport</li>
                            <li>Vehicle registration certificate</li>
                            <li>Insurance documents</li>
                        </ul>
                        
                        <p>Please contact the sacco office to arrange a convenient time for your visit and complete the registration process.</p>
                        
                        <p>Welcome to {join_request.sacco.name}!</p>
                        
                        <p>Best regards,<br>
                        The PSV Finder Team</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            plain_message = f"""
            PSV Finder - Request Approved!
            
            Dear {join_request.owner.get_full_name() or join_request.owner.username},
            
            Congratulations! Your join request to {join_request.sacco.name} has been approved.
            
            Vehicle: {join_request.vehicle.registration_number}
            Approval Date: {join_request.processed_at.strftime('%B %d, %Y at %I:%M %p')}
            
            Next Steps - Visit Sacco Office:
            Location: {join_request.sacco.location or 'Contact sacco for details'}
            Phone: {join_request.sacco.contact_number}
            
            Please contact the sacco to complete your registration.
            
            Welcome to {join_request.sacco.name}!
            
            Best regards,
            The PSV Finder Team
            """
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[join_request.owner.email],
                html_message=html_content,
                fail_silently=False,
            )
            
            logger.info(f"Approval notification email sent to {join_request.owner.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send approval notification email: {str(e)}")
            return False
    
    @staticmethod
    def send_rejection_notification(join_request, rejection_reason=None):
        """Send rejection notification to vehicle owner"""
        try:
            subject = f"PSV Finder - Update on Your Join Request"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #f44336; color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .rejection-box {{ background: #f8d7da; border: 1px solid #f5c6cb; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                    .location-box {{ background: white; padding: 20px; border-left: 4px solid #f44336; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🚌 PSV Finder</h1>
                        <h2>Request Update</h2>
                    </div>
                    <div class="content">
                        <p>Dear <strong>{join_request.owner.get_full_name() or join_request.owner.username}</strong>,</p>
                        
                        <div class="rejection-box">
                            <p>We regret to inform you that your request to join <strong>{join_request.sacco.name}</strong> has not been approved at this time.</p>
                        </div>
                        
                        <p><strong>Vehicle Registration:</strong> {join_request.vehicle.registration_number}</p>
                        <p><strong>Decision Date:</strong> {join_request.processed_at.strftime('%B %d, %Y at %I:%M %p')}</p>
                        
                        {"<p><strong>Reason:</strong> " + (rejection_reason or "No specific reason provided") + "</p>" if rejection_reason else ""}
                        
                        <div class="location-box">
                            <h3>📞 Contact Sacco for More Information:</h3>
                            <p><strong>Sacco Name:</strong> {join_request.sacco.name}</p>
                            <p><strong>Location:</strong> {join_request.sacco.location or 'Contact sacco for location details'}</p>
                            <p><strong>Phone:</strong> {join_request.sacco.contact_number}</p>
                            <p><strong>Email:</strong> {join_request.sacco.email or 'Not provided'}</p>
                        </div>
                        
                        <h3>What you can do:</h3>
                        <ul>
                            <li>Contact the sacco directly for detailed feedback</li>
                            <li>Address any concerns raised and reapply in the future</li>
                            <li>Explore other saccos that might be a better fit</li>
                        </ul>
                        
                        <p>Don't be discouraged! There are many other saccos available on PSV Finder that might be perfect for your vehicle.</p>
                        
                        <p>Best regards,<br>
                        The PSV Finder Team</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            plain_message = f"""
            PSV Finder - Request Update
            
            Dear {join_request.owner.get_full_name() or join_request.owner.username},
            
            Your join request to {join_request.sacco.name} has not been approved at this time.
            
            Vehicle: {join_request.vehicle.registration_number}
            Decision Date: {join_request.processed_at.strftime('%B %d, %Y at %I:%M %p')}
            
            {"Reason: " + (rejection_reason or "No specific reason provided") if rejection_reason else ""}
            
            Contact Sacco:
            Location: {join_request.sacco.location or 'Contact for details'}
            Phone: {join_request.sacco.contact_number}
            
            You can contact the sacco for more information or explore other options.
            
            Best regards,
            The PSV Finder Team
            """
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[join_request.owner.email],
                html_message=html_content,
                fail_silently=False,
            )
            
            logger.info(f"Rejection notification email sent to {join_request.owner.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send rejection notification email: {str(e)}")
            return False
    
    @staticmethod
    def send_admin_new_request_notification(join_request):
        """Send notification to sacco admin about new join request"""
        try:
            # Get the sacco admin from the sacco_admin field
            sacco_admin = join_request.sacco.sacco_admin
            
            if not sacco_admin:
                logger.warning(f"No admin assigned to sacco {join_request.sacco.name}")
                return False
            
            if not sacco_admin.email:
                logger.warning(f"Sacco admin {sacco_admin.username} has no email address")
                return False
            
            subject = f"🚌 PSV Finder - New Join Request for {join_request.sacco.name}"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #2196F3; color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .request-box {{ background: white; padding: 20px; border-left: 4px solid #2196F3; margin: 20px 0; }}
                    .owner-box {{ background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                    .vehicle-box {{ background: #f3e5f5; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                    .highlight {{ color: #2196F3; font-weight: bold; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🚌 PSV Finder Admin</h1>
                        <h2>New Join Request</h2>
                    </div>
                    <div class="content">
                        <p>Hello <strong>{sacco_admin.get_full_name() or sacco_admin.username}</strong>,</p>
                        
                        <p>You have received a new join request for <strong>{join_request.sacco.name}</strong> that requires your review.</p>
                        
                        <div class="request-box">
                            <h3>Request Details:</h3>
                            <p><strong>Request ID:</strong> #{join_request.id}</p>
                            <p><strong>Submission Date:</strong> {join_request.requested_at.strftime('%B %d, %Y at %I:%M %p')}</p>
                            <p><strong>Status:</strong> Pending Review</p>
                        </div>
                        
                        <div class="owner-box">
                            <h3>👤 Vehicle Owner Information:</h3>
                            <p><strong>Name:</strong> {join_request.owner.get_full_name() or join_request.owner.username}</p>
                            <p><strong>Email:</strong> {join_request.owner.email}</p>
                            <p><strong>Phone:</strong> {getattr(join_request.owner, 'phone_number', 'Not provided')}</p>
                        </div>
                        
                        <div class="vehicle-box">
                            <h3>🚗 Vehicle Information:</h3>
                            <p><strong>Registration:</strong> {join_request.vehicle.registration_number}</p>
                            <p><strong>Make:</strong> {getattr(join_request.vehicle, 'make', 'Not specified')}</p>
                            <p><strong>Model:</strong> {getattr(join_request.vehicle, 'model', 'Not specified')}</p>
                            <p><strong>Year:</strong> {getattr(join_request.vehicle, 'year', 'Not specified')}</p>
                            <p><strong>Capacity:</strong> {getattr(join_request.vehicle, 'passenger_capacity', 'Not specified')} passengers</p>
                        </div>
                        
                        <h3>Required Actions:</h3>
                        <ul>
                            <li>Review the vehicle documents</li>
                            <li>Verify owner credentials</li>
                            <li>Approve or reject the request</li>
                            <li>Notify the owner of your decision</li>
                        </ul>
                        
                        <p>Please log into your admin panel to review this request and make a decision.</p>
                        
                        <p><strong>Note:</strong> The vehicle owner has been notified that their request is under review.</p>
                        
                        <p>Best regards,<br>
                        The PSV Finder System</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            plain_message = f"""
            PSV Finder - New Join Request
            
            Hello {sacco_admin.get_full_name() or sacco_admin.username},
            
            You have a new join request for {join_request.sacco.name} to review:
            
            Request #: {join_request.id}
            Date: {join_request.requested_at.strftime('%B %d, %Y at %I:%M %p')}
            
            Owner: {join_request.owner.get_full_name() or join_request.owner.username}
            Email: {join_request.owner.email}
            
            Vehicle: {join_request.vehicle.registration_number}
            Make/Model: {getattr(join_request.vehicle, 'make', 'Not specified')} {getattr(join_request.vehicle, 'model', 'Not specified')}
            Year: {getattr(join_request.vehicle, 'year', 'Not specified')}
            
            Please review and process this request in your admin panel.
            
            Best regards,
            PSV Finder System
            """
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[sacco_admin.email],
                html_message=html_content,
                fail_silently=False,
            )
            
            logger.info(f"New request notification sent to sacco admin {sacco_admin.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send admin notification email: {str(e)}")
            return False
    
    @staticmethod
    def send_welcome_email(user):
        """Send welcome email to newly registered user"""
        try:
            subject = "🎉 Welcome to PSV Finder - Your Journey Starts Here!"
            
            # Create HTML email content
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #4CAF50, #45a049); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .welcome-box {{ background: #e8f5e8; border: 1px solid #c3e6cb; padding: 20px; border-radius: 5px; margin: 20px 0; text-align: center; }}
                    .feature-box {{ background: white; padding: 20px; border-left: 4px solid #4CAF50; margin: 20px 0; }}
                    .highlight {{ color: #4CAF50; font-weight: bold; }}
                    .emoji {{ font-size: 1.2em; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🚌 PSV Finder</h1>
                        <h2>Welcome Aboard!</h2>
                    </div>
                    <div class="content">
                        <div class="welcome-box">
                            <h2>🎉 Welcome to PSV Finder!</h2>
                            <p>Your account has been successfully created</p>
                        </div>
                        
                        <p>Dear <strong>{user.get_full_name() or user.username}</strong>,</p>
                        
                        <p>Thank you for joining PSV Finder, Kenya's premier platform for connecting vehicle owners with Sacco opportunities!</p>
                        
                        <div class="feature-box">
                            <h3>🚗 What You Can Do Now:</h3>
                            <p><span class="emoji">📋</span> <strong>Register Your Vehicles:</strong> Add your PSV details and documentation</p>
                            <p><span class="emoji">🔍</span> <strong>Find Saccos:</strong> Browse and search for Saccos that match your route and requirements</p>
                            <p><span class="emoji">📧</span> <strong>Submit Join Requests:</strong> Apply to join Saccos directly through our platform</p>
                            <p><span class="emoji">📊</span> <strong>Track Applications:</strong> Monitor the status of your join requests in real-time</p>
                        </div>
                        
                        <div class="feature-box">
                            <h3>🌟 Getting Started:</h3>
                            <p>1. <strong>Complete Your Profile:</strong> Add your contact information and preferences</p>
                            <p>2. <strong>Add Your Vehicle:</strong> Upload vehicle details and required documents</p>
                            <p>3. <strong>Explore Saccos:</strong> Browse available Saccos in your area</p>
                            <p>4. <strong>Submit Applications:</strong> Apply to join Saccos that interest you</p>
                        </div>
                        
                        <div class="feature-box">
                            <h3>📞 Need Help?</h3>
                            <p>Our support team is here to help you every step of the way:</p>
                            <p><strong>Email:</strong> support@psvfinder.com</p>
                            <p><strong>Phone:</strong> +254 XXX XXX XXX</p>
                            <p><strong>Hours:</strong> Monday - Friday, 8:00 AM - 6:00 PM</p>
                        </div>
                        
                        <p>We're excited to have you as part of the PSV Finder community. Together, we're making it easier for vehicle owners to find the right Sacco partnerships!</p>
                        
                        <p>Happy exploring!</p>
                        
                        <p>Best regards,<br>
                        <strong>The PSV Finder Team</strong></p>
                        
                        <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
                        <p style="font-size: 12px; color: #666; text-align: center;">
                            You received this email because you created an account on PSV Finder.<br>
                            If you have any questions, please contact our support team.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Plain text version
            plain_message = f"""
            Welcome to PSV Finder!
            
            Dear {user.get_full_name() or user.username},
            
            Thank you for joining PSV Finder, Kenya's premier platform for connecting vehicle owners with Sacco opportunities!
            
            What You Can Do Now:
            • Register Your Vehicles: Add your PSV details and documentation
            • Find Saccos: Browse and search for Saccos that match your requirements
            • Submit Join Requests: Apply to join Saccos directly through our platform
            • Track Applications: Monitor the status of your join requests
            
            Getting Started:
            1. Complete Your Profile: Add your contact information and preferences
            2. Add Your Vehicle: Upload vehicle details and required documents
            3. Explore Saccos: Browse available Saccos in your area
            4. Submit Applications: Apply to join Saccos that interest you
            
            Need Help?
            Email: support@psvfinder.com
            Phone: +254 XXX XXX XXX
            Hours: Monday - Friday, 8:00 AM - 6:00 PM
            
            We're excited to have you as part of the PSV Finder community!
            
            Best regards,
            The PSV Finder Team
            """
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_content,
                fail_silently=False,
            )
            
            logger.info(f"Welcome email sent to {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
            return False
    