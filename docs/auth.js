// auth.js - Authentication service
class AuthService {
    constructor(supabaseClient) {
      this.supabase = supabaseClient;
      this.currentUser = null;
      this.authCallbacks = [];
      
      // Listen for auth state changes
      this.supabase.auth.onAuthStateChange((event, session) => {
        this.currentUser = session?.user || null;
        this.notifyCallbacks(event, session);
        this.updateUI();
      });
      
      // Check current session on load
      this.getCurrentUser();
    }
  
    async getCurrentUser() {
      const { data: { session } } = await this.supabase.auth.getSession();
      this.currentUser = session?.user || null;
      this.updateUI();
      return this.currentUser;
    }
  
    async signUp(email, password, displayName) {
      const { data, error } = await this.supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            display_name: displayName
          }
        }
      });
      
      if (error) throw error;
      return data;
    }
  
    async signIn(email, password) {
      const { data, error } = await this.supabase.auth.signInWithPassword({
        email,
        password
      });
      
      if (error) throw error;
      return data;
    }
  
    async signInWithGoogle() {
      const { data, error } = await this.supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: window.location.origin
        }
      });
      
      if (error) throw error;
      return data;
    }
  
    async signOut() {
      const { error } = await this.supabase.auth.signOut();
      if (error) throw error;
    }
  
    async resetPassword(email) {
      const { error } = await this.supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/reset-password.html`
      });
      
      if (error) throw error;
    }
  
    async updateProfile(updates) {
      if (!this.currentUser) throw new Error('Not authenticated');
      
      const { error } = await this.supabase
        .from('user_profiles')
        .upsert({
          id: this.currentUser.id,
          ...updates,
          updated_at: new Date().toISOString()
        });
      
      if (error) throw error;
    }
  
    async getUserProfile() {
      if (!this.currentUser) return null;
      
      const { data, error } = await this.supabase
        .from('user_profiles')
        .select('*')
        .eq('id', this.currentUser.id)
        .single();
      
      if (error && error.code !== 'PGRST116') throw error;
      return data;
    }
  
    onAuthStateChange(callback) {
      this.authCallbacks.push(callback);
    }
  
    notifyCallbacks(event, session) {
      this.authCallbacks.forEach(callback => callback(event, session));
    }
  
    updateUI() {
      // Update navigation based on auth state
      const authElements = document.querySelectorAll('[data-auth]');
      authElements.forEach(element => {
        const authState = element.getAttribute('data-auth');
        if (authState === 'authenticated' && this.currentUser) {
          element.style.display = '';
        } else if (authState === 'unauthenticated' && !this.currentUser) {
          element.style.display = '';
        } else {
          element.style.display = 'none';
        }
      });
  
      // Update user info
      const userNameElements = document.querySelectorAll('[data-user-name]');
      userNameElements.forEach(element => {
        if (this.currentUser) {
          element.textContent = this.currentUser.user_metadata?.display_name || 
                               this.currentUser.email || 'User';
        }
      });
    }
  
    isAuthenticated() {
      return !!this.currentUser;
    }
  
    requireAuth() {
      if (!this.isAuthenticated()) {
        window.location.href = 'login.html';
        return false;
      }
      return true;
    }
  }
  
  // Initialize auth service globally
  window.authService = new AuthService(supabaseClient);