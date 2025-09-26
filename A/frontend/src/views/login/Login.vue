<template>
  <v-main class="white-bg center-content">
    <div class="login-container">

        <div class="logo">
        <img src="@/assets/images/2.png" width="150" height="150">
        </div>

        <div class="center-box">
            <h2 class="login-title">เข้าสู่ระบบ</h2>
        </div>
        
        <form @submit.prevent="handleLogin">
            <!-- username-->>
            <div class="form-group">
                <label for="username">username :</label>
                <input type="text" id="username" v-model="username" required />
            </div>

            <!-- password -->>
             <div class="form-group">
                <label for="password">password :</label>
                <input type="password" id="password" v-model="password" required />
             </div>

             <button class="login-btn" type="submit" :disabled="loading" >{{ loading ? "กำลังเข้าสู่ระบบ..." : "เข้าสู่ระบบ"}}</button>
        </form>
    </div>

  </v-main>
  
</template>

<script setup>
import { ref } from "vue";
const loading = ref(false);
const username = ref("");
const password = ref("");

const handleLogin = async() =>{
    loading.value = true;
};
</script>

<style scoped>

</style>