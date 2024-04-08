<template>
  <div id="app" class="ui container">
    <h2 class="ui header">Register</h2>
    <form class="ui form" @submit.prevent="register">
      <div class="field">
        <label>Select Authentication Method</label>
        <div class="ui toggle checkbox">
          <input type="checkbox" v-model="lineSelected" checked>
          <label>
            <i class="line icon"></i> LINE
          </label>
        </div>
        <div class="ui toggle checkbox">
          <input type="checkbox" v-model="youtubeSelected" checked>
          <label>
            <i class="youtube icon"></i> YouTube
          </label>
        </div>
      </div>

      <div class="field">
        <label for="email">Email:</label>
        <input type="email" id="email" v-model="email" required>
      </div>

      <div class="field">
        <label for="name">Name:</label>
        <input type="text" id="name" v-model="name" required>
      </div>

      <div class="field">
        <label for="phone">Phone:</label>
        <input type="tel" id="phone" v-model="phone" required>
      </div>

      <button class="ui button" type="submit">Register</button>
    </form>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      lineSelected: true,
      youtubeSelected: true,
      email: '',
      name: '',
      phone: '',
    };
  },
  methods: {
    async register() {
      try {
        const response = await axios.post('/api/register', {
          lineSelected: this.lineSelected,
          youtubeSelected: this.youtubeSelected,
          email: this.email,
          name: this.name,
          phone: this.phone,
        });

        if (response.data.success) {
          // Registration successful
          // Redirect user or show success message
        } else {
          // Registration failed
          // Show error message
        }
      } catch (error) {
        console.error(error);
      }
    },
  },
};
</script>