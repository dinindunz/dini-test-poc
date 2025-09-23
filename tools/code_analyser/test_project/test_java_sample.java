// Java Sample for Testing Code Analysis Tools
package com.example.user;

import java.util.List;
import java.util.Optional;
import java.util.Date;
import java.util.regex.Pattern;

public interface UserRepository {
    Optional<User> findById(Long id);
    User save(User user);
    boolean deleteById(Long id);
    List<User> findAll();
}

public class User {
    private Long id;
    private String name;
    private String email;
    private Date createdAt;

    public User() {
        this.createdAt = new Date();
    }

    public User(String name, String email) {
        this();
        this.name = name;
        this.email = email;
    }

    // Getters and setters
    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public Date getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(Date createdAt) {
        this.createdAt = createdAt;
    }

    @Override
    public String toString() {
        return "User{" +
                "id=" + id +
                ", name='" + name + '\'' +
                ", email='" + email + '\'' +
                ", createdAt=" + createdAt +
                '}';
    }
}

public class DatabaseUserRepository implements UserRepository {
    private Connection connection;

    public DatabaseUserRepository(Connection connection) {
        this.connection = connection;
    }

    @Override
    public Optional<User> findById(Long id) {
        String sql = "SELECT * FROM users WHERE id = ?";

        try (PreparedStatement stmt = connection.prepareStatement(sql)) {
            stmt.setLong(1, id);
            ResultSet rs = stmt.executeQuery();

            if (rs.next()) {
                return Optional.of(mapRowToUser(rs));
            }

            return Optional.empty();
        } catch (SQLException e) {
            throw new RuntimeException("Error finding user by id", e);
        }
    }

    @Override
    public User save(User user) {
        if (user.getId() == null) {
            return insertUser(user);
        } else {
            return updateUser(user);
        }
    }

    @Override
    public boolean deleteById(Long id) {
        String sql = "DELETE FROM users WHERE id = ?";

        try (PreparedStatement stmt = connection.prepareStatement(sql)) {
            stmt.setLong(1, id);
            int rowsAffected = stmt.executeUpdate();
            return rowsAffected > 0;
        } catch (SQLException e) {
            throw new RuntimeException("Error deleting user", e);
        }
    }

    @Override
    public List<User> findAll() {
        String sql = "SELECT * FROM users ORDER BY id";
        List<User> users = new ArrayList<>();

        try (PreparedStatement stmt = connection.prepareStatement(sql);
             ResultSet rs = stmt.executeQuery()) {

            while (rs.next()) {
                users.add(mapRowToUser(rs));
            }

            return users;
        } catch (SQLException e) {
            throw new RuntimeException("Error finding all users", e);
        }
    }

    private User insertUser(User user) {
        String sql = "INSERT INTO users (name, email, created_at) VALUES (?, ?, ?)";

        try (PreparedStatement stmt = connection.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS)) {
            stmt.setString(1, user.getName());
            stmt.setString(2, user.getEmail());
            stmt.setTimestamp(3, new Timestamp(user.getCreatedAt().getTime()));

            stmt.executeUpdate();

            try (ResultSet keys = stmt.getGeneratedKeys()) {
                if (keys.next()) {
                    user.setId(keys.getLong(1));
                }
            }

            return user;
        } catch (SQLException e) {
            throw new RuntimeException("Error inserting user", e);
        }
    }

    private User updateUser(User user) {
        String sql = "UPDATE users SET name = ?, email = ? WHERE id = ?";

        try (PreparedStatement stmt = connection.prepareStatement(sql)) {
            stmt.setString(1, user.getName());
            stmt.setString(2, user.getEmail());
            stmt.setLong(3, user.getId());

            stmt.executeUpdate();
            return user;
        } catch (SQLException e) {
            throw new RuntimeException("Error updating user", e);
        }
    }

    private User mapRowToUser(ResultSet rs) throws SQLException {
        User user = new User();
        user.setId(rs.getLong("id"));
        user.setName(rs.getString("name"));
        user.setEmail(rs.getString("email"));
        user.setCreatedAt(rs.getTimestamp("created_at"));
        return user;
    }
}

public class UserService {
    private UserRepository userRepository;
    private static final Pattern EMAIL_PATTERN =
        Pattern.compile("^[A-Za-z0-9+_.-]+@([A-Za-z0-9.-]+\\.[A-Za-z]{2,})$");

    public UserService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    public User createUser(String name, String email) {
        if (!isValidEmail(email)) {
            throw new IllegalArgumentException("Invalid email format");
        }

        User user = new User(name, email);
        return userRepository.save(user);
    }

    public Optional<User> getUserById(Long id) {
        return userRepository.findById(id);
    }

    public User updateUser(User user) {
        if (!isValidEmail(user.getEmail())) {
            throw new IllegalArgumentException("Invalid email format");
        }

        return userRepository.save(user);
    }

    public boolean deleteUser(Long id) {
        return userRepository.deleteById(id);
    }

    public List<User> getAllUsers() {
        return userRepository.findAll();
    }

    private boolean isValidEmail(String email) {
        return email != null && EMAIL_PATTERN.matcher(email).matches();
    }
}

public class Main {
    public static void main(String[] args) {
        // Example usage
        System.out.println("User Management System");

        // Initialise repository and service
        Connection connection = getConnection();
        UserRepository userRepository = new DatabaseUserRepository(connection);
        UserService userService = new UserService(userRepository);

        // Create a new user
        User newUser = userService.createUser("John Doe", "john.doe@example.com");
        System.out.println("Created user: " + newUser);

        // Get user by ID
        Optional<User> retrievedUser = userService.getUserById(newUser.getId());
        if (retrievedUser.isPresent()) {
            System.out.println("Retrieved user: " + retrievedUser.get());
        }

        // Get all users
        List<User> allUsers = userService.getAllUsers();
        System.out.println("Total users: " + allUsers.size());
    }

    private static Connection getConnection() {
        // Database connection logic would go here
        return null;
    }
}