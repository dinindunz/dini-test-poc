# Feature Request Scenarios for Code Analyser Testing

Here are few feature request scenarios that will test the code analyser's ability to find the right files to modify:

## 1. User Profile Enhancement

*"Add a user profile picture upload feature with image validation and storage"*

**Expected Analysis**: Should identify `User.java` entity, `UserService.java`, `UserController.java`, and potentially create new utility classes for image handling.

## 2. Product Inventory Alerts

*"Implement automatic email notifications when product stock falls below a configurable threshold"*

**Expected Analysis**: Should find `Product.java`, `ProductService.java`, identify the `reduceStock()` method, and suggest creating notification service classes.

## 3. Order Status Tracking

*"Add a new 'PREPARING' status between 'CONFIRMED' and 'SHIPPED' in the order workflow"*

**Expected Analysis**: Should identify `Order.java` enum, `OrderService.java` (if it existed), `OrderRepository.java`, and any controllers that handle order status updates.

## 4. Category-based Discounts

*"Create a discount system where products can have percentage discounts based on their category"*

**Expected Analysis**: Should identify `Product.java`, `Category.java`, `ProductService.java`, `ProductController.java`, and suggest creating new discount-related entities.

## 5. User Role Management

*"Add a new 'MODERATOR' role that can manage product reviews but not user accounts"*

**Expected Analysis**: Should find `User.java` enum, `UserService.java`, security configuration, and review-related functionality.

## 6. Advanced Product Search

*"Implement multi-criteria search with filters for price range, category, rating, and availability"*

**Expected Analysis**: Should identify `ProductRepository.java`, `ProductService.java`, `ProductController.java`, and existing search methods to enhance.

## 7. Order History Export

*"Allow users to export their order history as PDF or CSV files"*

**Expected Analysis**: Should find `OrderRepository.java`, `UserController.java`, `Order.java` relationships, and suggest creating export utility classes.

## 8. Product Bundle Feature

*"Create product bundles where multiple products can be sold together at a discounted price"*

**Expected Analysis**: Should identify `Product.java`, `OrderItem.java`, `ProductService.java`, and suggest creating new bundle entities and relationships.

## 9. Review Moderation System

*"Add admin functionality to approve/reject product reviews before they become visible"*

**Expected Analysis**: Should find `ProductReview.java`, identify admin-related controllers, and suggest adding moderation workflow.

## 10. Wishlist Feature

*"Allow users to save products to a wishlist for future purchase"*

**Expected Analysis**: Should identify `User.java`, `Product.java` relationships, and suggest creating new wishlist entity and service layer.

---

## Testing Goals

These scenarios test the code analyser's ability to:

- Find relevant entities and their relationships
- Identify service layer methods that need modification
- Locate controller endpoints that handle related functionality
- Understand business logic flow across multiple files
- Suggest new files that need to be created
- Map dependencies between different layers

Try one of these with the code analyser to see how well it identifies the minimal set of files that need to be read and modified!